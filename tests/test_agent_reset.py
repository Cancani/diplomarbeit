from contextlib import redirect_stdout
from copy import deepcopy
import io
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapter.kubevirt_manifest import NAMESPACE, infrastructure, manifests, resource_name
from adapter.vertrag import AdapterError
from agent.lebenszyklus import reset
from agent.zustand import StateError, StateStore
from modell.validierung import load_model
from test_kubevirt_delete import DeletingCluster
from test_kubevirt_lifecycle import http_endpoint


class ResetCluster(DeletingCluster):
    def __init__(self):
        super().__init__()
        self.serial = 0

    def put(self, resource):
        resource = deepcopy(resource)
        self.serial += 1
        resource['metadata'].setdefault('uid', f'uid-{self.serial}')
        return super().put(resource)


class AgentResetTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)/'state.sqlite3'
        self.config = {'stateFile': self.path, 'adapters': {'kubevirt': {
            'command': 'unused', 'args': [], 'timeoutSeconds': 30}}}
        self.model = load_model(ROOT/'modell/beispiele/referenz.yaml')
        self.store = StateStore(self.path)
        self.store.start_create('run-01', 'create-01', 'kubevirt', self.model)
        self.cluster = ResetCluster()
        for resource in infrastructure():
            self.cluster._request('create', [], time.monotonic() + 15, resource)
        for resource in manifests('run-01', 'create-01', self.model):
            self.cluster.put(resource)
        self.store.observe_resources('run-01', 'create-01', self.cluster.status('run-01')['resources'])
        self.store.advance('run-01', 'create-01', 'ready')
        self.original = self.store.get('run-01')
        self.calls = []
        self.url = None

    def call(self, adapter, tool, arguments, schema):
        self.calls.append(tool)
        record = StateStore(self.path).get('run-01')
        self.assertEqual(record['model_hash'], self.original['model_hash'])
        self.assertEqual(record['model_snapshot'], self.original['model_snapshot'])
        if tool == 'delete':
            self.assertEqual(record['phase'], 'deleting')
            return self.cluster.delete(**arguments)
        if tool == 'create':
            self.assertEqual(record['phase'], 'creating')
            self.assertEqual(record['operation']['stage'], 'creating')
            old_ids = {r['resource_id'] for r in self.original['resources']}
            self.assertFalse(old_ids & {r['resource_id'] for r in record['resources']})
            self.assertEqual(arguments['model'], self.original['model_snapshot'])
            result = self.cluster.create(**arguments)
            self.assertLessEqual(sum(r['kind'] == 'VirtualMachine' for r in self.cluster.objects.values()), 1)
            return result
        self.assertEqual(tool, 'status')
        actual = self.cluster.status(arguments['run_id'])
        if {r['kind'] for r in actual['resources']} >= {'VirtualMachine', 'Service'}:
            actual.update(vmReady=True, vmState='Running', vmiPhase='Running', httpUrl=self.url)
        return actual

    def vm_uid(self):
        return self.cluster.objects[('virtualmachine', NAMESPACE, resource_name('run-01'))]['metadata']['uid']

    def test_reset_uses_snapshot_and_same_id_only_reads_while_new_id_recreates(self):
        old_uid = self.vm_uid()
        with http_endpoint() as self.url, patch('agent.lebenszyklus.call_tool', side_effect=self.call), \
                patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()):
            reset(self.config, 'run-01', 'reset-01')
            first_uid = self.vm_uid()
            self.assertNotEqual(first_uid, old_uid)
            calls = len(self.calls)
            reset(self.config, 'run-01', 'reset-01')
            self.assertEqual(self.calls[calls:], ['status'])
            self.assertEqual(self.vm_uid(), first_uid)
            reset(self.config, 'run-01', 'reset-02')
            self.assertNotEqual(self.vm_uid(), first_uid)
        record = self.store.get('run-01')
        self.assertEqual(record['phase'], 'ready')
        self.assertEqual(record['operation']['operation_id'], 'reset-02')
        self.assertEqual(record['operation']['status'], 'succeeded')

    def test_failed_cleanup_keeps_inventory_and_same_id_resumes_before_creation(self):
        def failed_cleanup(adapter, tool, arguments, schema):
            if tool == 'delete':
                raise AdapterError('timeout')
            return self.call(adapter, tool, arguments, schema)

        with patch('agent.lebenszyklus.call_tool', side_effect=failed_cleanup), \
                redirect_stdout(io.StringIO()), self.assertRaises(AdapterError):
            reset(self.config, 'run-01', 'reset-01')
        record = self.store.get('run-01')
        self.assertEqual((record['phase'], record['operation']['stage']), ('error', 'deleting'))
        self.assertEqual(record['resources'], self.original['resources'])
        self.assertNotIn('create', self.calls)
        with self.assertRaises(StateError), redirect_stdout(io.StringIO()):
            reset(self.config, 'run-01', 'other-reset')
        with http_endpoint() as self.url, patch('agent.lebenszyklus.call_tool', side_effect=self.call), \
                patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()):
            reset(self.config, 'run-01', 'reset-01')
        self.assertEqual(self.store.get('run-01')['phase'], 'ready')

    def test_lost_create_response_resumes_without_another_cleanup_or_duplicate_vm(self):
        def lost_response(adapter, tool, arguments, schema):
            result = self.call(adapter, tool, arguments, schema)
            if tool == 'create':
                raise AdapterError('timeout')
            return result

        with patch('agent.lebenszyklus.call_tool', side_effect=lost_response), \
                patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()), \
                self.assertRaises(AdapterError):
            reset(self.config, 'run-01', 'reset-01')
        record = StateStore(self.path).get('run-01')
        self.assertEqual((record['phase'], record['operation']['stage']), ('error', 'creating'))
        created_uid = self.vm_uid()
        self.assertIn(created_uid, {r['resource_id'] for r in record['resources']})
        self.model['vm']['resources']['minMemoryMiB'] += 1024
        self.calls.clear()
        with http_endpoint() as self.url, patch('agent.lebenszyklus.call_tool', side_effect=self.call), \
                patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()):
            reset(self.config, 'run-01', 'reset-01')
        self.assertEqual(self.vm_uid(), created_uid)
        self.assertNotIn('delete', self.calls)

    def test_final_cleanup_check_rejects_false_complete_response(self):
        count = 0

        def incomplete(adapter, tool, arguments, schema):
            nonlocal count
            if tool == 'delete':
                count += 1
                if count == 1:
                    return {'complete': True, 'resources': [], 'removed': arguments['resources']}
                raise AdapterError('timeout')
            return self.call(adapter, tool, arguments, schema)

        with patch('agent.lebenszyklus.call_tool', side_effect=incomplete), \
                patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()), \
                self.assertRaises(AdapterError):
            reset(self.config, 'run-01', 'reset-01')
        self.assertNotIn('create', self.calls)
        self.assertEqual(self.store.get('run-01')['resources'], self.original['resources'])

    def test_abandoned_guarded_reset_resumes_both_stages_after_read_only_reconciliation(self):
        class ProcessGone(BaseException):
            pass

        for stage in ('deleting', 'creating'):
            operation_id = 'reset-' + stage

            def abandoned(adapter, tool, arguments, schema):
                if stage == 'deleting' and tool == 'delete':
                    raise ProcessGone()
                result = self.call(adapter, tool, arguments, schema)
                if stage == 'creating' and tool == 'create':
                    raise ProcessGone()  # Plattformänderung ohne gespeicherte Antwort.
                return result

            with self.subTest(stage=stage), patch('agent.lebenszyklus.call_tool', side_effect=abandoned), \
                    patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()):
                with self.assertRaises(ProcessGone):
                    reset(self.config, 'run-01', operation_id)
            record = self.store.get('run-01')
            self.assertEqual(record['operation']['status'], 'running')
            self.assertEqual(record['operation']['stage'], stage)
            self.assertEqual(record['operation']['guarded'], 1)
            self.calls.clear()

            def reconcile_first(adapter, tool, arguments, schema):
                if not self.calls:
                    self.assertEqual(tool, 'status')
                    self.assertEqual(self.store.get('run-01')['operation']['status'], 'running')
                return self.call(adapter, tool, arguments, schema)

            with http_endpoint() as self.url, patch('agent.lebenszyklus.call_tool', side_effect=reconcile_first), \
                    patch('agent.lebenszyklus.time.sleep'), redirect_stdout(io.StringIO()):
                reset(self.config, 'run-01', operation_id)
            self.assertEqual(self.store.get('run-01')['phase'], 'ready')
            if stage == 'creating':
                self.assertNotIn('delete', self.calls)


if __name__ == '__main__':
    unittest.main()

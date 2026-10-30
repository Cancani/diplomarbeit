from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
from pathlib import Path
import sys
import tempfile
import time
from threading import Thread
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapter.kubevirt_lifecycle import KubeVirtLifecycle
from adapter.kubevirt_manifest import NAMESPACE, infrastructure, manifests, resource_name
from adapter.vertrag import AdapterError
from agent.lebenszyklus import create, service_ready
from agent.zustand import StateStore
from modell.validierung import load_model


class MemoryCluster(KubeVirtLifecycle):
    """Nur ein API-Testbestand, keine Simulation einer laufenden VM."""
    def __init__(self):
        super().__init__(['unused'], 15)
        self.objects = {}
        self.writes = []

    def put(self, resource):
        item = deepcopy(resource)
        metadata = item['metadata']
        metadata.setdefault('uid', 'uid-' + str(len(self.objects)))
        self.objects[(item['kind'].lower(), metadata.get('namespace'), metadata['name'])] = item
        return item

    def _object(self, kind, name, deadline, namespace=None):
        return self.objects.get((kind.lower(), namespace, name))

    def _get(self, arguments, deadline):
        types = {'virtualmachines': 'VirtualMachine', 'virtualmachineinstances': 'VirtualMachineInstance',
                 'datavolumes': 'DataVolume', 'persistentvolumeclaims': 'PersistentVolumeClaim',
                 'services': 'Service', 'pods': 'Pod', 'endpointslices': 'EndpointSlice'}
        requested = {types[name] for name in arguments[0].split(',')}
        return [v for v in self.objects.values()
                if v['kind'] in requested and v['metadata'].get('namespace') == NAMESPACE]

    def _request(self, verb, arguments, deadline, document=None, allow_empty=False):
        if verb != 'create':
            raise AssertionError(verb)
        self.writes.append(deepcopy(document))
        item = self.put(document)
        if item['kind'] == 'ResourceQuota':
            item['status'] = {'hard': item['spec']['hard'],
                              'used': {k: '0' for k in item['spec']['hard']}}
        return item


@contextmanager
def http_endpoint(code=200, body=b'lernumgebung bereit\n', delay=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(code)
            if code == 302:
                self.send_header('Location', '/redirected')
            self.end_headers()
            try:
                if delay is None:
                    self.wfile.write(body)
                else:
                    for value in body:
                        self.wfile.write(bytes([value]))
                        self.wfile.flush()
                        time.sleep(delay)
            except OSError:
                pass  # Ein abgelehnter oder abgebrochener Check darf die Verbindung schliessen.

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=lambda: server.serve_forever(poll_interval=0.05), daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class KubeVirtLifecycleTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)/'zustand.sqlite3'
        self.model = load_model(ROOT/'modell/beispiele/referenz.yaml')
        self.config = {'stateFile': self.path, 'adapters': {'kubevirt': {
            'command': 'unused', 'args': [], 'timeoutSeconds': 30}}}

    def test_manifest_maps_model_and_limits_count_on_the_api_server(self):
        self.model['vm']['resources'] = {'minVcpus': 4, 'minMemoryMiB': 4096, 'minDiskGiB': 20}
        vm, service = manifests('run-01', 'operation-01', self.model)
        spec = vm['spec']
        domain = spec['template']['spec']['domain']
        self.assertEqual(domain['cpu']['cores'], 4)
        self.assertEqual(domain['memory']['guest'], '4096Mi')
        self.assertEqual(spec['dataVolumeTemplates'][0]['spec']['storage']['resources']['requests']['storage'], '20Gi')
        cloud = yaml.safe_load(spec['template']['spec']['volumes'][1]['cloudInitNoCloud']['userData'])
        self.assertFalse(cloud['ssh_pwauth'])
        self.assertEqual(cloud['users'][0]['ssh_authorized_keys'], self.model['vm']['ssh']['publicKeys'])
        self.assertIn('User=nobody', cloud['write_files'][1]['content'])
        self.assertEqual(service['spec']['selector'], spec['template']['metadata']['labels'])
        self.assertTrue(all('nodePort' not in port for port in service['spec']['ports']))
        self.assertEqual(infrastructure()[1]['spec']['hard'], {
            'count/virtualmachines.kubevirt.io': '30', 'count/virtualmachineinstances.kubevirt.io': '30'})
        with self.assertRaises(AdapterError):
            manifests('../foreign', 'operation-01', self.model)

    def test_each_create_step_mutates_at_most_one_object_and_repetition_is_idempotent(self):
        cluster = MemoryCluster()
        results = []
        for _ in range(4):
            before = len(cluster.writes)
            results.append(cluster.create('run-01', 'operation-01', self.model))
            self.assertEqual(len(cluster.writes) - before, 1)
        self.assertEqual([r['complete'] for r in results], [False, False, False, True])
        self.assertEqual([r['kind'] for r in results[2]['resources']], ['VirtualMachine'])
        self.assertEqual([r['kind'] for r in results[3]['resources']], ['VirtualMachine', 'Service'])
        self.assertTrue(cluster.create('run-01', 'operation-01', self.model)['complete'])
        self.assertEqual(len(cluster.writes), 4)

    def test_capacity_and_foreign_resource_conflicts_prevent_vm_creation(self):
        cluster = MemoryCluster()
        for _ in range(2):
            cluster.create('run-01', 'operation-01', self.model)
        for index in range(30):
            cluster.put({'kind': 'VirtualMachine', 'metadata': {
                'name': f'existing-{index}', 'namespace': NAMESPACE}})
        with self.assertRaises(AdapterError) as caught:
            cluster.create('run-01', 'operation-01', self.model)
        self.assertEqual(caught.exception.code, 'capacity_limit')
        self.assertEqual(len(cluster.writes), 2)
        foreign = MemoryCluster()
        foreign.put({'kind': 'Namespace', 'metadata': {'name': NAMESPACE}})
        with self.assertRaises(AdapterError) as caught:
            foreign.create('run-01', 'operation-01', self.model)
        self.assertEqual(caught.exception.code, 'resource_conflict')
        self.assertEqual(foreign.writes, [])

    def test_inventory_follows_owners_and_records_pv_without_adopting_base_storage(self):
        cluster = MemoryCluster()
        cluster.put(infrastructure()[0])
        vm, service = manifests('run-01', 'operation-01', self.model)
        vm['metadata']['uid'] = 'vm-id'
        vm['status'] = {'ready': True, 'printableStatus': 'Running'}
        cluster.put(vm)
        service['metadata']['uid'] = 'service-id'
        service['spec']['ports'][0]['nodePort'] = 30022
        service['spec']['ports'][1]['nodePort'] = 30080
        cluster.put(service)
        cluster.put({'kind': 'EndpointSlice', 'metadata': {
            'name': 'service-endpoints', 'namespace': NAMESPACE, 'uid': 'endpoints-id',
            'ownerReferences': [{'uid': 'service-id'}]}})
        for kind, uid, parent in [('VirtualMachineInstance', 'vmi-id', 'vm-id'),
                                  ('DataVolume', 'dv-id', 'vm-id'),
                                  ('PersistentVolumeClaim', 'pvc-id', 'dv-id'),
                                  ('Pod', 'pod-id', 'vmi-id')]:
            item = {'kind': kind, 'metadata': {'name': resource_name('run-01'), 'namespace': NAMESPACE,
                    'uid': uid, 'ownerReferences': [{'uid': parent}]}}
            if kind == 'VirtualMachineInstance':
                item['status'] = {'phase': 'Running', 'nodeName': 'node-01'}
            if kind == 'PersistentVolumeClaim':
                item['spec'] = {'volumeName': 'run-pv'}
            cluster.put(item)
        cluster.put({'kind': 'PersistentVolume', 'metadata': {'name': 'run-pv', 'uid': 'pv-id'},
                     'spec': {'claimRef': {'uid': 'pvc-id', 'namespace': NAMESPACE, 'name': resource_name('run-01')}}})
        cluster.put({'kind': 'PersistentVolumeClaim', 'metadata': {
            'name': 'data-claim', 'namespace': NAMESPACE, 'uid': 'base-pvc'}})
        cluster.put({'kind': 'Node', 'metadata': {'name': 'node-01'},
                     'status': {'addresses': [{'type': 'InternalIP', 'address': '10.0.21.197'}]}})
        actual = cluster.status('run-01')
        self.assertEqual({r['resource_id'] for r in actual['resources']},
                         {'vm-id', 'service-id', 'endpoints-id', 'vmi-id', 'dv-id', 'pvc-id', 'pod-id', 'pv-id'})
        self.assertEqual(actual['httpUrl'], 'http://10.0.21.197:30080/')
        self.assertEqual(actual['sshPort'], 30022)
        self.assertTrue(actual['vmReady'])

    def test_agent_persists_before_following_step_and_repeated_create_only_reads(self):
        vm = {'kind': 'VirtualMachine', 'name': 'vm', 'scope': NAMESPACE, 'resource_id': 'vm-id'}
        service = {'kind': 'Service', 'name': 'vm', 'scope': NAMESPACE, 'resource_id': 'service-id'}
        calls = []
        with http_endpoint() as url:
            def call(adapter, tool, arguments, schema):
                record = StateStore(self.path).get('run-01')
                self.assertEqual(record['model_snapshot'], self.model)
                calls.append(tool)
                if tool == 'create':
                    if calls.count('create') == 1:
                        self.assertEqual(record['resources'], [])
                        return {'complete': False, 'resources': [vm]}
                    self.assertEqual(record['resources'][0]['resource_id'], 'vm-id')
                    return {'complete': True, 'resources': [vm, service]}
                return {'resources': [vm, service], 'vmState': 'Running', 'vmiPhase': 'Running',
                        'vmReady': True, 'modelHash': record['model_hash'], 'httpUrl': url,
                        'sshHost': '127.0.0.1', 'sshPort': 30022}

            with patch('agent.lebenszyklus.call_tool', side_effect=call), redirect_stdout(io.StringIO()):
                self.assertTrue(create(self.config, 'run-01', 'operation-01', 'kubevirt', self.model)[1])
                self.assertTrue(create(self.config, 'run-01', 'new-operation', 'kubevirt', self.model)[1])
        record = StateStore(self.path).get('run-01')
        self.assertEqual(record['phase'], 'ready')
        self.assertEqual(record['operation']['operation_id'], 'operation-01')
        self.assertEqual(calls, ['create', 'create', 'status', 'status'])

    def test_timeout_reconciles_resources_from_a_lost_create_response(self):
        vm = {'kind': 'VirtualMachine', 'name': 'vm', 'scope': NAMESPACE, 'resource_id': 'vm-id'}

        def call(adapter, tool, arguments, schema):
            if tool == 'create':
                raise AdapterError('timeout')
            return {'resources': [vm], 'vmState': 'Starting', 'vmiPhase': 'Pending',
                    'vmReady': False, 'modelHash': StateStore(self.path).get('run-01')['model_hash'],
                    'httpUrl': None, 'sshHost': None, 'sshPort': None}

        with patch('agent.lebenszyklus.call_tool', side_effect=call), redirect_stdout(io.StringIO()):
            with self.assertRaises(AdapterError):
                create(self.config, 'run-01', 'operation-01', 'kubevirt', self.model)
        record = StateStore(self.path).get('run-01')
        self.assertEqual(record['phase'], 'error')
        self.assertEqual(record['operation']['error_code'], 'timeout')
        self.assertEqual(record['resources'], [vm])

    def test_http_readiness_rejects_wrong_content_redirect_and_oversized_body(self):
        for code, body, expected in [(200, b'lernumgebung bereit\n', True), (200, b'wrong', False),
                                     (302, b'', False), (200, b'x' * 4097, False)]:
            with self.subTest(code=code, body_length=len(body)), http_endpoint(code, body) as url:
                self.assertEqual(service_ready(url, self.model), expected)
        with http_endpoint(delay=0.05) as url:
            started = time.monotonic()
            self.assertFalse(service_ready(url, self.model, timeout=0.15))
            self.assertLess(time.monotonic() - started, 1)



if __name__ == '__main__':
    unittest.main()

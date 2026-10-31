import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapter.kubevirt_provider import KubeVirtProvider
from adapter.vertrag import AdapterError, read_status_response, CREATE_SCHEMA, RUN_STATUS_SCHEMA, DELETE_SCHEMA
from agent.mcp_client import platform_status, call_tool
from modell.validierung import load_model
from gemeinsam.prozessschutz import run_guard


class McpStatusTests(unittest.TestCase):
    def config(self, mode, *arguments, timeout=10):
        return {'command': sys.executable,
                'args': [str(ROOT/'tests/fixtures/mcp_adapter.py'), mode, *map(str, arguments)],
                'timeoutSeconds': timeout}

    def test_real_stdio_round_trip_through_cli_creates_no_database(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root/'config.yaml'
            config.write_text(yaml.safe_dump({
                'stateFile': 'must-not-exist.sqlite3',
                'adapters': {'kubevirt': self.config('success')},
            }), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, '-m', 'agent', '--config', str(config),
                 'platform-status', '--platform', 'kubevirt'],
                cwd=root, env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='cp1252'),
                capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data['protocolVersion'])
            self.assertEqual(data['status']['nodes'], [{'name': 'test-node', 'ready': True}])
            self.assertEqual(set(root.iterdir()), {config})
            created = call_tool(self.config('success'), 'create', {
                'run_id': 'test-run', 'operation_id': 'test-operation',
                'model': load_model(ROOT/'modell/beispiele/referenz.yaml')}, CREATE_SCHEMA)
            self.assertTrue(created['complete'])
            self.assertEqual(created['resources'][0]['resource_id'], 'test-uid')
            actual = call_tool(self.config('success'), 'status', {'run_id': 'test-run'}, RUN_STATUS_SCHEMA)
            self.assertFalse(actual['vmReady'])
            self.assertIsNone(actual['httpUrl'])
            removed = call_tool(self.config('success'), 'delete', {
                'run_id': 'test-run', 'operation_id': 'delete-operation',
                'resources': created['resources']}, DELETE_SCHEMA)
            self.assertTrue(removed['complete'])
            self.assertEqual(removed['removed'], created['resources'])

    def test_adapter_errors_and_invalid_responses_are_not_reported_as_success(self):
        for mode, code in [('invalid', 'invalid_response'), ('error', 'platform_error')]:
            with self.subTest(mode=mode), self.assertRaises(AdapterError) as caught:
                platform_status(self.config(mode))
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))
        with self.assertRaises(AdapterError) as caught:
            platform_status({'command': str(ROOT/'missing-program'), 'args': [], 'timeoutSeconds': 2})
        self.assertEqual(caught.exception.code, 'transport_error')

    def test_timeout_during_handshake_stops_the_child_process(self):
        with tempfile.TemporaryDirectory() as folder:
            heartbeat = Path(folder)/'heartbeat.txt'
            started = time.monotonic()
            with self.assertRaises(AdapterError) as caught:
                platform_status(self.config('silent', heartbeat, timeout=2))
            self.assertEqual(caught.exception.code, 'timeout')
            self.assertLess(time.monotonic() - started, 12)
            self.assertTrue(heartbeat.exists(), 'Der Testprozess muss tatsächlich gestartet worden sein.')
            stopped = heartbeat.read_text(encoding='utf-8')
            time.sleep(0.3)
            self.assertEqual(heartbeat.read_text(encoding='utf-8'), stopped)

    def test_guard_participation_is_required_before_calling_the_requested_tool(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with run_guard(root/'state.sqlite3', 'test-run') as session:
                result = platform_status({**self.config('success'), '_processGuard': session})
                self.assertEqual(result['status']['kubevirtPhase'], 'Deployed')
                for mode in ('missing-guard', 'wrong-guard'):
                    marker = root/mode
                    with self.subTest(mode=mode), self.assertRaises(AdapterError):
                        platform_status({**self.config(mode, marker), '_processGuard': session})
                    self.assertFalse(marker.exists(), 'Ohne passende Sitzung darf das Zielwerkzeug nicht laufen.')

    def test_provider_only_issues_get_requests_and_keeps_vm_state_separate(self):
        documents = [
            {'items': [{'metadata': {'name': 'dl-test'}, 'status': {
                'conditions': [{'type': 'Ready', 'status': 'True'}]}}]},
            {'items': [{'status': {'phase': 'Deployed'}}]},
            {'items': [
                {'kind': 'VirtualMachine', 'metadata': {'name': 'vm', 'namespace': 'lab', 'uid': 'vm-id'},
                 'status': {'printableStatus': 'Stopped'}},
                {'kind': 'VirtualMachineInstance', 'metadata': {'name': 'vm', 'namespace': 'lab', 'uid': 'vmi-id'},
                 'status': {'phase': 'Running'}},
            ]},
        ]
        replies = [subprocess.CompletedProcess([], 0, json.dumps(d), '') for d in documents]
        with patch('adapter.kubevirt_provider.subprocess.run', side_effect=replies) as run:
            status = KubeVirtProvider(['microk8s', 'kubectl'], 15).platform_status()
        self.assertEqual(status['virtualMachines'][0]['state'], 'Stopped')
        self.assertEqual(status['virtualMachineInstances'][0]['state'], 'Running')
        self.assertEqual(read_status_response({'ok': True, 'status': status}), status)
        self.assertEqual(run.call_count, 3)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][:3], ['microk8s', 'kubectl', 'get'])
            self.assertEqual(call.args[0][-3:-1], ['-o', 'json'])
            self.assertGreater(call.kwargs['timeout'], 0)
            self.assertNotIn('shell', call.kwargs)

    def test_provider_failures_do_not_echo_command_output(self):
        failures = [
            (FileNotFoundError(), 'command_not_found'),
            (subprocess.TimeoutExpired('kubectl', 1), 'timeout'),
            (subprocess.CompletedProcess([], 1, 'PRIVATE-CONTENT', 'PRIVATE-CONTENT'), 'platform_error'),
            (subprocess.CompletedProcess([], 0, 'PRIVATE-CONTENT', ''), 'invalid_response'),
            (subprocess.CompletedProcess([], 0, '{"items": {}}', ''), 'invalid_response'),
        ]
        for failure, code in failures:
            arguments = {'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure}
            with self.subTest(code=code), patch('adapter.kubevirt_provider.subprocess.run', **arguments):
                with self.assertRaises(AdapterError) as caught:
                    KubeVirtProvider(['microk8s', 'kubectl'], 15).platform_status()
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))


if __name__ == '__main__':
    unittest.main()

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import boto3
from botocore.stub import Stubber
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapter.aws import run_status
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

    def test_aws_run_status_keeps_non_instance_resources_after_termination(self):
        region = 'us-east-1'
        run_id = 'aws-test-01'
        digest = 'a' * 64
        client = boto3.client('ec2', region_name=region,
                              aws_access_key_id='test', aws_secret_access_key='test')
        filters = {'Filters': [{'Name': 'tag:ManagedBy', 'Values': ['diplomarbeit-agent']},
                               {'Name': 'tag:RunId', 'Values': [run_id]}]}
        tags = [{'Key': 'ManagedBy', 'Value': 'diplomarbeit-agent'},
                {'Key': 'RunId', 'Value': run_id}, {'Key': 'ModelHash', 'Value': digest}]
        for state in ('running', 'terminated'):
            with self.subTest(state=state), Stubber(client) as ec2:
                instance = {'InstanceId': 'i-0123456789abcdef0', 'State': {'Name': state},
                            'PublicIpAddress': '192.0.2.10', 'Tags': tags}
                ec2.add_response('describe_instances', {'Reservations': [{'Instances': [instance]}]}, filters)
                ec2.add_response('describe_volumes', {'Volumes': [{'VolumeId': 'vol-0123', 'Tags': tags}]}, filters)
                ec2.add_response('describe_network_interfaces', {'NetworkInterfaces': [
                    {'NetworkInterfaceId': 'eni-0123', 'TagSet': tags}]}, filters)
                ec2.add_response('describe_security_groups', {'SecurityGroups': [
                    {'GroupId': 'sg-0123', 'Tags': tags}]}, filters)

                result = run_status(client, region, run_id)
                ec2.assert_no_pending_responses()
                expected = ['EBSVolume', 'NetworkInterface', 'SecurityGroup']
                if state == 'running':
                    expected.insert(0, 'EC2Instance')
                self.assertEqual([item['kind'] for item in result['resources']], expected)
                self.assertEqual(result['modelHash'], digest)
                self.assertEqual(result['vmReady'], state == 'running')
                self.assertEqual(result['httpUrl'], 'http://192.0.2.10:8080/' if state == 'running' else None)

    def test_aws_status_reads_all_pages_for_configured_profile_without_database(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            aws = root/'aws_status.py'
            aws.write_text(
                """import boto3
from botocore.stub import Stubber
from unittest.mock import patch

from adapter.aws import main

client = boto3.client('ec2', region_name='us-east-1',
                      aws_access_key_id='test', aws_secret_access_key='test')
filters = [{'Name': 'tag:ManagedBy', 'Values': ['diplomarbeit-agent']}]
with Stubber(client) as stubber, patch('boto3.Session') as session:
    stubber.add_response('describe_instances', {'Reservations': [], 'NextToken': 'page2'},
                         {'Filters': filters})
    stubber.add_response('describe_instances', {'Reservations': [{'Instances': [
        {'InstanceId': 'i-0123456789abcdef0', 'State': {'Name': 'running'}}
    ]}]}, {'Filters': filters, 'NextToken': 'page2'})

    def connect(*, profile_name, region_name):
        assert (profile_name, region_name) == ('diplomarbeit', 'us-east-1')
        return session.return_value

    session.side_effect = connect
    session.return_value.client.return_value = client
    main()
""", encoding='utf-8')
            config = root/'config.yaml'
            config.write_text(yaml.safe_dump({
                'stateFile': 'must-not-exist.sqlite3',
                'adapters': {'aws': {'command': sys.executable, 'timeoutSeconds': 10,
                                     'args': ['-c', 'import runpy, sys; runpy.run_path(sys.argv.pop(1))',
                                              str(aws), '--profile', 'diplomarbeit', '--region', 'us-east-1']}},
            }), encoding='utf-8')
            command = [sys.executable, '-m', 'agent', '--config', str(config),
                       'platform-status', '--platform', 'aws']
            options = dict(cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=20)
            result = subprocess.run([*command, '--json'], **options)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], {
                'platform': 'aws', 'region': 'us-east-1',
                'instances': [{'id': 'i-0123456789abcdef0', 'state': 'running'}],
            })
            result = subprocess.run(command, **options)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Vom Agenten gekennzeichnete EC2-Instanzen: 1', result.stdout)
            self.assertFalse((root/'must-not-exist.sqlite3').exists())

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
                 'platform-status', '--platform', 'kubevirt', '--json'],
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

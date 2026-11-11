from base64 import b64decode
from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import boto3
from botocore.stub import ANY, Stubber
import yaml

from adapter.aws import _create_step
from adapter.vertrag import AdapterError
from agent.cli import build_parser, run as run_command
from agent.zustand import StateStore
from modell.snapshot import encode_snapshot
from modell.validierung import load_model


class AwsCreateTests(unittest.TestCase):
    def test_cli_resumes_aws_reset_from_saved_phases(self):
        definition = Path(__file__).resolve().parents[1] / 'modell/beispiele/referenz.yaml'
        model = load_model(definition)
        _, digest = encode_snapshot(model)
        resource = {'kind': 'EC2Instance', 'name': 'i-0123', 'resource_id': 'i-0123', 'scope': 'us-east-1'}
        replacement = {**resource, 'name': 'i-0124', 'resource_id': 'i-0124'}
        inventory = []
        calls = []
        failures = {'check_reset': 'aws_image_unavailable', 'delete': 'timeout', 'create': 'timeout'}

        def call(adapter, tool, arguments, schema):
            calls.append(tool)
            if tool == 'check_reset':
                if error := failures.pop(tool, None):
                    raise AdapterError(error)
                return {}
            self.assertEqual(arguments['run_id'], 'aws-test-01')
            if tool == 'create':
                self.assertEqual(arguments['model'], model)
                if arguments['operation_id'] == 'create-01':
                    inventory.append(resource)
                else:
                    self.assertEqual(arguments['operation_id'], 'reset-01')
                    self.assertNotIn(resource, inventory)
                    if not inventory:
                        inventory.append(replacement)
                    if error := failures.pop(tool, None):
                        raise AdapterError(error)
                return {'complete': True, 'resources': inventory.copy()}
            if tool == 'delete':
                self.assertEqual(arguments['model_hash'], digest)
                self.assertEqual(arguments['resources'], inventory)
                if error := failures.pop(tool, None):
                    raise AdapterError(error)
                removed = inventory.copy()
                inventory.clear()
                return {'complete': True, 'resources': [], 'removed': removed}
            phase = 'Running' if inventory else 'Absent'
            return {'resources': inventory.copy(), 'vmState': phase, 'vmiPhase': phase,
                    'vmReady': bool(inventory), 'modelHash': digest if inventory else None,
                    'httpUrl': 'http://192.0.2.10:8080/' if inventory else None,
                    'sshHost': None, 'sshPort': None}

        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.sqlite3'
            config = Path(folder) / 'agent.yaml'
            config.write_text(yaml.safe_dump({'stateFile': state.name, 'adapters': {
                'aws': {'command': 'unused', 'args': [], 'timeoutSeconds': 30},
            }}), encoding='utf-8')
            parser = build_parser()

            def invoke(command, *arguments):
                return run_command(parser.parse_args([
                    '--config', str(config), command, '--run-id', 'aws-test-01', *arguments,
                ]))

            with patch('agent.lebenszyklus.call_tool', side_effect=call), \
                    patch('agent.lebenszyklus.service_ready', return_value=True), \
                    patch('sys.stderr', new=io.StringIO()), redirect_stdout(io.StringIO()):
                self.assertEqual(invoke('create', str(definition), '--platform', 'aws',
                                        '--operation-id', 'create-01'), 0)
                self.assertEqual(invoke('status'), 0)
                store = StateStore(state)
                calls.clear()
                self.assertEqual(invoke('reset', '--operation-id', 'reset-01'), 1)
                self.assertEqual(calls, ['check_reset'])
                self.assertEqual(store.get('aws-test-01')['phase'], 'ready')

                self.assertEqual(invoke('reset', '--operation-id', 'reset-01'), 1)
                record = store.get('aws-test-01')
                self.assertEqual((record['phase'], record['operation']['stage']), ('error', 'deleting'))
                self.assertEqual(record['resources'], [resource])

                self.assertEqual(invoke('reset', '--operation-id', 'reset-01'), 1)
                record = store.get('aws-test-01')
                self.assertEqual((record['phase'], record['operation']['stage']), ('error', 'creating'))
                self.assertEqual(record['resources'], [replacement])

                calls.clear()
                self.assertEqual(invoke('reset', '--operation-id', 'reset-01'), 0)
                self.assertEqual(calls, ['check_reset', 'create', 'status'])
                record = store.get('aws-test-01')
                self.assertEqual((record['phase'], record['model_hash']), ('ready', digest))
                self.assertEqual(record['resources'], [replacement])

                calls.clear()
                self.assertEqual(invoke('reset', '--operation-id', 'reset-01'), 0)
                self.assertEqual(calls, ['status'])
                self.assertEqual(invoke('delete', '--operation-id', 'delete-01'), 0)
                self.assertEqual(store.get('aws-test-01')['phase'], 'absent')

    def test_launch_saves_ids_and_reuses_one_instance_with_restricted_http(self):
        region = 'us-east-1'
        run, operation = 'aws-test-01', 'create-test-01'
        vpc, subnet, cidr = 'vpc-0123', 'subnet-0123', '8.8.8.8/32'
        network = (vpc, subnet, cidr)
        model = load_model(Path(__file__).resolve().parents[1] / 'modell/beispiele/referenz.yaml')
        _, digest = encode_snapshot(model)
        name = 'da-' + hashlib.sha256(run.encode()).hexdigest()[:24]
        image = 'ami-0fa5967347d08d2df'
        tags = [{'Key': key, 'Value': value} for key, value in {
            'ManagedBy': 'diplomarbeit-agent', 'RunId': run, 'ModelHash': digest,
            'OperationId': operation,
            'LaunchConfig': hashlib.sha256(f'{vpc}/{subnet}/{cidr}/{image}'.encode()).hexdigest(),
        }.items()]
        filters = {'Filters': [{'Name': 'tag:ManagedBy', 'Values': ['diplomarbeit-agent']},
                               {'Name': 'tag:RunId', 'Values': [run]}]}
        group = {'GroupId': 'sg-0123', 'GroupName': name, 'VpcId': vpc, 'Tags': tags, 'IpPermissions': []}
        permission = {'IpProtocol': 'tcp', 'FromPort': 8080, 'ToPort': 8080,
                      'IpRanges': [{'CidrIp': cidr}]}
        instance = {'InstanceId': 'i-0123', 'SubnetId': subnet, 'VpcId': vpc, 'ImageId': image,
                    'InstanceType': 't3.small', 'State': {'Name': 'pending'}, 'Tags': tags,
                    'SecurityGroups': [{'GroupId': 'sg-0123'}],
                    'BlockDeviceMappings': [{'DeviceName': '/dev/sda1', 'Ebs': {'VolumeId': 'vol-0123'}}],
                    'NetworkInterfaces': [{'NetworkInterfaceId': 'eni-0123'}]}
        client = boto3.client('ec2', region_name=region,
                              aws_access_key_id='test', aws_secret_access_key='test')

        def describe(stub, groups=(), instances=(), disks=(), interfaces=()):
            reservations = [{'Instances': list(instances)}] if instances else []
            stub.add_response('describe_instances', {'Reservations': reservations}, filters)
            stub.add_response('describe_volumes', {'Volumes': list(disks)}, filters)
            stub.add_response('describe_network_interfaces', {'NetworkInterfaces': list(interfaces)}, filters)
            stub.add_response('describe_security_groups', {'SecurityGroups': list(groups)}, filters)

        # Das SDK kodiert die Cloud-init-Daten für die AWS-Anfrage.
        user_data = []
        client.meta.events.register('before-parameter-build.ec2.RunInstances',
                                    lambda params, **_: user_data.append(params['UserData']),
                                    unique_id='capture-cloud-init')
        with Stubber(client) as stub:
            describe(stub)
            stub.add_response('describe_subnets', {'Subnets': [{'SubnetId': subnet, 'VpcId': vpc,
                                                                'State': 'available'}]},
                              {'SubnetIds': [subnet]})
            stub.add_response('create_security_group', {'GroupId': 'sg-0123'}, {
                'GroupName': name, 'Description': 'Diplomarbeit HTTP test', 'VpcId': vpc,
                'TagSpecifications': [{'ResourceType': 'security-group', 'Tags': tags}],
            })
            result = _create_step(client, region, network, run, operation, model)
            self.assertEqual([item['resource_id'] for item in result['resources']], ['sg-0123'])
            self.assertFalse(result['complete'])

            describe(stub, groups=[group])
            stub.add_response('authorize_security_group_ingress', {},
                              {'GroupId': 'sg-0123', 'IpPermissions': [permission]})
            self.assertFalse(_create_step(client, region, network, run, operation, model)['complete'])

            group = {**group, 'IpPermissions': [permission]}
            describe(stub, groups=[group])
            stub.add_response('run_instances', {'Instances': [instance]}, {
                'ImageId': image, 'InstanceType': 't3.small', 'MinCount': 1, 'MaxCount': 1,
                'ClientToken': hashlib.sha256(f'{run}/{operation}'.encode()).hexdigest(),
                'UserData': ANY, 'MetadataOptions': {'HttpTokens': 'required'},
                'CreditSpecification': {'CpuCredits': 'standard'},
                'BlockDeviceMappings': [{'DeviceName': '/dev/sda1', 'Ebs': {
                    'VolumeSize': 12, 'VolumeType': 'gp3', 'DeleteOnTermination': True,
                }}],
                'NetworkInterfaces': [{'DeviceIndex': 0, 'SubnetId': subnet, 'Groups': ['sg-0123'],
                                       'AssociatePublicIpAddress': True, 'DeleteOnTermination': True}],
                'TagSpecifications': [{'ResourceType': kind, 'Tags': tags}
                                      for kind in ('instance', 'volume', 'network-interface')],
            })
            result = _create_step(client, region, network, run, operation, model)
            self.assertEqual({item['resource_id'] for item in result['resources']},
                             {'sg-0123', 'i-0123', 'vol-0123', 'eni-0123'})
            self.assertFalse(result['complete'])

            describe(stub, groups=[group], instances=[instance],
                     disks=[{'VolumeId': 'vol-0123', 'Tags': tags}],
                     interfaces=[{'NetworkInterfaceId': 'eni-0123', 'TagSet': tags}])
            self.assertTrue(_create_step(client, region, network, run, operation, model)['complete'])
            stub.assert_no_pending_responses()

        self.assertEqual(len(user_data), 1)
        cloud = yaml.safe_load(b64decode(user_data[0]))
        self.assertEqual(cloud['users'][0]['ssh_authorized_keys'], model['vm']['ssh']['publicKeys'])
        self.assertEqual(cloud['write_files'][0]['content'], 'lernumgebung bereit\n')

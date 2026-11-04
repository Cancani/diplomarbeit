import unittest

import boto3
from botocore.stub import Stubber

from adapter.aws import _delete_step
from adapter.vertrag import AdapterError


REGION = 'us-east-1'
RUN = 'aws-test-01'
MODEL_HASH = 'a' * 64
TAGS = [{'Key': 'ManagedBy', 'Value': 'diplomarbeit-agent'},
        {'Key': 'RunId', 'Value': RUN}, {'Key': 'ModelHash', 'Value': MODEL_HASH}]
FILTERS = {'Filters': [{'Name': 'tag:ManagedBy', 'Values': ['diplomarbeit-agent']},
                       {'Name': 'tag:RunId', 'Values': [RUN]}]}


def resource(kind, resource_id):
    return {'kind': kind, 'name': resource_id, 'resource_id': resource_id, 'scope': REGION}


class AwsDeleteTests(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('ec2', region_name=REGION,
                                   aws_access_key_id='test', aws_secret_access_key='test')

    def test_delete_waits_for_confirmation_and_removes_only_saved_resources(self):
        vm = resource('EC2Instance', 'i-0123')
        volume = resource('EBSVolume', 'vol-0123')
        interface = resource('NetworkInterface', 'eni-0123')
        group = resource('SecurityGroup', 'sg-0123')
        all_resources = [vm, volume, interface, group]
        instance = {'InstanceId': 'i-0123', 'State': {'Name': 'running'}, 'Tags': TAGS}
        disk = {'VolumeId': 'vol-0123', 'State': 'available', 'Tags': TAGS}
        nic = {'NetworkInterfaceId': 'eni-0123', 'Status': 'available', 'TagSet': TAGS}
        security_group = {'GroupId': 'sg-0123', 'Tags': TAGS}

        with Stubber(self.client) as stub:
            self.inventory(stub, [instance], [disk], [nic], [security_group])
            self.assertEqual(_delete_step(self.client, REGION, RUN, MODEL_HASH, [vm]), {
                'complete': False, 'resources': all_resources, 'removed': [],
            })

            self.inventory(stub, [instance], [disk], [nic], [security_group])
            stub.add_response('terminate_instances', {}, {'InstanceIds': ['i-0123']})
            self.assertEqual(_delete_step(self.client, REGION, RUN, MODEL_HASH, all_resources), {
                'complete': False, 'resources': all_resources, 'removed': [],
            })

            stub.add_response('describe_instances', {'Reservations': []}, FILTERS)
            self.absent_by_id(stub, 'describe_instances', 'Reservations', 'instance-id', 'i-0123')
            stub.add_response('describe_volumes', {'Volumes': [disk]}, FILTERS)
            stub.add_response('describe_network_interfaces', {'NetworkInterfaces': [nic]}, FILTERS)
            stub.add_response('describe_security_groups', {'SecurityGroups': [security_group]}, FILTERS)
            stub.add_response('delete_volume', {}, {'VolumeId': 'vol-0123'})
            stub.add_response('delete_network_interface', {}, {'NetworkInterfaceId': 'eni-0123'})
            self.assertEqual(_delete_step(self.client, REGION, RUN, MODEL_HASH, all_resources), {
                'complete': False, 'resources': [volume, interface, group], 'removed': [vm],
            })

            stub.add_response('describe_instances', {'Reservations': []}, FILTERS)
            stub.add_response('describe_volumes', {'Volumes': []}, FILTERS)
            self.absent_by_id(stub, 'describe_volumes', 'Volumes', 'volume-id', 'vol-0123')
            stub.add_response('describe_network_interfaces', {'NetworkInterfaces': []}, FILTERS)
            self.absent_by_id(stub, 'describe_network_interfaces', 'NetworkInterfaces',
                              'network-interface-id', 'eni-0123')
            stub.add_response('describe_security_groups', {'SecurityGroups': [security_group]}, FILTERS)
            stub.add_response('delete_security_group', {}, {'GroupId': 'sg-0123'})
            self.assertEqual(_delete_step(self.client, REGION, RUN, MODEL_HASH, [volume, interface, group]), {
                'complete': False, 'resources': [group], 'removed': [volume, interface],
            })

            self.inventory(stub)
            self.absent_by_id(stub, 'describe_security_groups', 'SecurityGroups', 'group-id', 'sg-0123')
            self.assertEqual(_delete_step(self.client, REGION, RUN, MODEL_HASH, [group]), {
                'complete': True, 'resources': [], 'removed': [group],
            })
            stub.assert_no_pending_responses()

    def test_known_resource_without_ownership_tags_is_a_conflict(self):
        with Stubber(self.client) as stub:
            stub.add_response('describe_instances', {'Reservations': []}, FILTERS)
            stub.add_response('describe_volumes', {'Volumes': []}, FILTERS)
            stub.add_response('describe_volumes', {'Volumes': [{'VolumeId': 'vol-0123'}]},
                              {'Filters': [{'Name': 'volume-id', 'Values': ['vol-0123']}]})
            with self.assertRaises(AdapterError) as error:
                _delete_step(self.client, REGION, RUN, MODEL_HASH, [resource('EBSVolume', 'vol-0123')])
            self.assertEqual(error.exception.code, 'resource_conflict')
            stub.assert_no_pending_responses()

    def inventory(self, stub, instances=(), disks=(), interfaces=(), groups=()):
        reservations = [{'Instances': list(instances)}] if instances else []
        stub.add_response('describe_instances', {'Reservations': reservations}, FILTERS)
        stub.add_response('describe_volumes', {'Volumes': list(disks)}, FILTERS)
        stub.add_response('describe_network_interfaces', {'NetworkInterfaces': list(interfaces)}, FILTERS)
        stub.add_response('describe_security_groups', {'SecurityGroups': list(groups)}, FILTERS)

    def absent_by_id(self, stub, operation, field, name, value):
        stub.add_response(operation, {field: []}, {'Filters': [{'Name': name, 'Values': [value]}]})

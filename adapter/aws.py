"""EC2-Ressourcen über Boto3 und MCP verwalten."""
import argparse
import hashlib
from ipaddress import IPv4Address, IPv4Network
import os
import re

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ConnectTimeoutError, ReadTimeoutError
from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.cloud_init import cloud_init
from adapter.kubevirt_manifest import resource_name, validate_id
from adapter.vertrag import (AdapterError, CREATE_SCHEMA, DELETE_SCHEMA, RUN_STATUS_SCHEMA,
                             read_result, read_status_response)
from gemeinsam.prozessschutz import GUARD_TOKEN, ProcessGuardError, adapter_guard
from modell.snapshot import encode_snapshot


MANAGED_BY = 'diplomarbeit-agent'
IMAGE_ID = 'ami-0fa5967347d08d2df'
INSTANCE_TYPE = 't3.small'
INSTANCE_STATES = {
    'pending': 'Provisioning', 'running': 'Running', 'shutting-down': 'Terminating',
    'stopping': 'Stopping', 'stopped': 'Stopped',
}
RESOURCE_TYPES = {
    'EC2Instance': ('InstanceId', 'instance-id', 'describe_instances', 'Reservations'),
    'EBSVolume': ('VolumeId', 'volume-id', 'describe_volumes', 'Volumes'),
    'NetworkInterface': ('NetworkInterfaceId', 'network-interface-id',
                         'describe_network_interfaces', 'NetworkInterfaces'),
    'SecurityGroup': ('GroupId', 'group-id', 'describe_security_groups', 'SecurityGroups'),
}
RESOURCE_PREFIXES = {'EC2Instance': 'i', 'EBSVolume': 'vol',
                     'NetworkInterface': 'eni', 'SecurityGroup': 'sg'}


def _tag_filters(run_id=None):
    tags = {'ManagedBy': MANAGED_BY}
    if run_id is not None:
        tags['RunId'] = run_id
    return [{'Name': f'tag:{key}', 'Values': [value]} for key, value in tags.items()]


def _describe(client, operation, key, filters):
    pages = client.get_paginator(operation).paginate(Filters=filters)
    return [item for page in pages for item in page[key]]


def _instances(client, filters):
    reservations = _describe(client, 'describe_instances', 'Reservations', filters)
    return [instance for reservation in reservations for instance in reservation['Instances']]


def _resource_items(client, kind, filters):
    _, _, operation, key = RESOURCE_TYPES[kind]
    if kind == 'EC2Instance':
        return [item for item in _instances(client, filters) if item['State']['Name'] != 'terminated']
    return _describe(client, operation, key, filters)


def _tags(kind, item):
    return {tag['Key']: tag['Value'] for tag in item.get('TagSet' if kind == 'NetworkInterface' else 'Tags', [])}


def _resource(kind, resource_id, region):
    return {'kind': kind, 'name': resource_id, 'resource_id': resource_id, 'scope': region}


def _inventory(client, region, run_id, known=()):
    resources = {}
    for kind, (id_key, id_filter, _, _) in RESOURCE_TYPES.items():
        items = _resource_items(client, kind, _tag_filters(run_id))
        visible_ids = {item[id_key] for item in items}
        missing_ids = sorted({key[1] for key in known if key[0] == kind} - visible_ids)
        if missing_ids:
            items.extend(_resource_items(client, kind, [{'Name': id_filter, 'Values': missing_ids}]))
        for item in items:
            tags = _tags(kind, item)
            digest = tags.get('ModelHash', '')
            if (tags.get('ManagedBy') != MANAGED_BY or tags.get('RunId') != run_id
                    or not re.fullmatch(r'[0-9a-f]{64}', digest)):
                raise AdapterError('resource_conflict')
            resource_id = item[id_key]
            resource = _resource(kind, resource_id, region)
            resources[kind, resource_id] = resource, item, digest
    if len({entry[2] for entry in resources.values()}) > 1:
        raise AdapterError('resource_conflict')
    return resources


def run_status(client, region, run_id):
    """Aktive Instanz und unabhängig davon alle markierten Nebenressourcen erfassen."""
    validate_id(run_id)
    inventory = _inventory(client, region, run_id)
    instances = [item for (kind, _), (_, item, _) in inventory.items() if kind == 'EC2Instance']
    if len(instances) > 1:
        raise AdapterError('resource_conflict')
    instance = instances[0] if instances else {}
    state = INSTANCE_STATES[instance['State']['Name']] if instance else 'Absent'
    ready = state == 'Running'
    ip = instance.get('PublicIpAddress')
    http_url = f'http://{IPv4Address(ip)}:8080/' if ready and ip else None
    digest = next((entry[2] for entry in inventory.values()), None)
    return {'resources': [entry[0] for entry in inventory.values()], 'vmState': state,
            'vmiPhase': state, 'vmReady': ready, 'modelHash': digest, 'httpUrl': http_url,
            'sshHost': None, 'sshPort': None}


def _create_step(client, region, network, run_id, operation_id, model):
    validate_id(run_id)
    validate_id(operation_id)
    _, digest = encode_snapshot(model)
    vpc_id, subnet_id, source = network
    name = resource_name(run_id)
    vm = model['vm']
    limits = vm['resources']
    user_data = cloud_init(name, vm)
    if (limits['minVcpus'] > 2 or limits['minMemoryMiB'] > 2048
            or limits['minDiskGiB'] > 100 or len(user_data.encode('utf-8')) > 16384):
        raise AdapterError('aws_model_unsupported')
    launch_config = hashlib.sha256(f'{vpc_id}/{subnet_id}/{source}/{IMAGE_ID}'.encode()).hexdigest()
    expected = {'ManagedBy': MANAGED_BY, 'RunId': run_id, 'ModelHash': digest,
                'OperationId': operation_id, 'LaunchConfig': launch_config}
    tags = [{'Key': key, 'Value': value} for key, value in expected.items()]

    inventory = _inventory(client, region, run_id)
    for (kind, _), (_, item, _) in inventory.items():
        if not expected.items() <= _tags(kind, item).items():
            raise AdapterError('resource_conflict')
    resources = [entry[0] for entry in inventory.values()]
    groups = [entry[1] for (kind, _), entry in inventory.items() if kind == 'SecurityGroup']
    instances = [entry[1] for (kind, _), entry in inventory.items() if kind == 'EC2Instance']
    if len(groups) > 1 or len(instances) > 1 or (inventory and not groups):
        raise AdapterError('resource_conflict')
    if not groups:
        subnets = client.describe_subnets(SubnetIds=[subnet_id])['Subnets']
        if len(subnets) != 1 or subnets[0]['VpcId'] != vpc_id or subnets[0]['State'] != 'available':
            raise AdapterError('resource_conflict')
        try:
            group = client.create_security_group(
                GroupName=name, Description='Diplomarbeit HTTP test', VpcId=vpc_id,
                TagSpecifications=[{'ResourceType': 'security-group', 'Tags': tags}],
            )
        except ClientError as error:
            if error.response['Error']['Code'] != 'InvalidGroup.Duplicate':
                raise
        else:
            resources.append(_resource('SecurityGroup', group['GroupId'], region))
        return {'complete': False, 'resources': resources}

    group = groups[0]
    if group['VpcId'] != vpc_id or group['GroupName'] != name:
        raise AdapterError('resource_conflict')
    group_id = group['GroupId']
    permission = {'IpProtocol': 'tcp', 'FromPort': 8080, 'ToPort': 8080, 'IpRanges': [{'CidrIp': source}]}
    rules = [{key: value for key, value in rule.items() if value != []}
             for rule in group.get('IpPermissions', [])]
    if not rules and not instances:
        try:
            client.authorize_security_group_ingress(GroupId=group_id, IpPermissions=[permission])
        except ClientError as error:
            if error.response['Error']['Code'] != 'InvalidPermission.Duplicate':
                raise
        return {'complete': False, 'resources': resources}
    if rules != [permission]:
        raise AdapterError('resource_conflict')
    if instances:
        instance = instances[0]
        if (instance['SubnetId'] != subnet_id or instance['VpcId'] != vpc_id
                or instance['ImageId'] != IMAGE_ID or instance['InstanceType'] != INSTANCE_TYPE
                or {item['GroupId'] for item in instance['SecurityGroups']} != {group_id}
                or instance['State']['Name'] not in ('pending', 'running')):
            raise AdapterError('resource_conflict')
        attached = _attached_resources(instance, region)
        ready = (len(attached) == 2
                 and all((item['kind'], item['resource_id']) in inventory for item in attached))
        return {'complete': ready, 'resources': resources}
    if len(resources) > 1:
        # Datenträger und Netzwerkschnittstelle können vor der Instanz sichtbar sein.
        return {'complete': False, 'resources': resources}

    token = hashlib.sha256(f'{run_id}/{operation_id}'.encode()).hexdigest()
    response = client.run_instances(
        ImageId=IMAGE_ID, InstanceType=INSTANCE_TYPE, MinCount=1, MaxCount=1, ClientToken=token,
        UserData=user_data, MetadataOptions={'HttpTokens': 'required'},
        CreditSpecification={'CpuCredits': 'standard'},
        BlockDeviceMappings=[{'DeviceName': '/dev/sda1', 'Ebs': {
            'VolumeSize': int(limits['minDiskGiB']), 'VolumeType': 'gp3', 'DeleteOnTermination': True,
        }}],
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': subnet_id, 'Groups': [group_id],
                            'AssociatePublicIpAddress': True, 'DeleteOnTermination': True}],
        TagSpecifications=[{'ResourceType': kind, 'Tags': tags}
                           for kind in ('instance', 'volume', 'network-interface')],
    )
    instance, = response['Instances']
    resources.append(_resource('EC2Instance', instance['InstanceId'], region))
    resources.extend(_attached_resources(instance, region))
    return {'complete': False, 'resources': resources}


def _attached_resources(instance, region):
    return ([_resource('EBSVolume', disk['Ebs']['VolumeId'], region)
             for disk in instance.get('BlockDeviceMappings', []) if disk.get('Ebs', {}).get('VolumeId')]
            + [_resource('NetworkInterface', interface['NetworkInterfaceId'], region)
               for interface in instance.get('NetworkInterfaces', [])])


def _delete_step(client, region, run_id, model_hash, resources):
    validate_id(run_id)
    if not re.fullmatch(r'[0-9a-f]{64}', model_hash):
        raise AdapterError('invalid_request')
    known = {}
    for resource in resources:
        kind, resource_id = resource['kind'], resource['resource_id']
        if kind not in RESOURCE_TYPES or resource['scope'] != region:
            raise AdapterError('resource_conflict')
        prefix = RESOURCE_PREFIXES[kind]
        if not re.fullmatch(rf'{prefix}-[0-9a-f]+', resource_id):
            raise AdapterError('invalid_request')
        known[kind, resource_id] = resource
    inventory = _inventory(client, region, run_id, known)
    if any(entry[2] != model_hash for entry in inventory.values()):
        raise AdapterError('resource_conflict')
    instances = [entry[1] for (kind, _), entry in inventory.items() if kind == 'EC2Instance']
    if len(instances) > 1:
        raise AdapterError('resource_conflict')
    result = {'complete': not inventory, 'resources': [entry[0] for entry in inventory.values()],
              'removed': [resource for key, resource in known.items() if key not in inventory]}
    if inventory.keys() - known.keys():
        # Der Agent muss neu entdeckte IDs vor dem ersten Löschaufruf speichern.
        return result
    if instances:
        instance = instances[0]
        if instance['State']['Name'] != 'shutting-down':
            _request_removal(client.terminate_instances, 'InvalidInstanceID.NotFound',
                             InstanceIds=[instance['InstanceId']])
    else:
        for (kind, resource_id), (_, item, _) in inventory.items():
            if kind == 'EBSVolume' and item['State'] == 'available':
                _request_removal(client.delete_volume, 'InvalidVolume.NotFound', 'VolumeInUse',
                                 VolumeId=resource_id)
            elif kind == 'NetworkInterface' and item['Status'] == 'available':
                _request_removal(client.delete_network_interface, 'InvalidNetworkInterfaceID.NotFound',
                                 'InvalidNetworkInterface.InUse', NetworkInterfaceId=resource_id)
            elif kind == 'SecurityGroup' and not any(key[0] == 'NetworkInterface' for key in inventory):
                _request_removal(client.delete_security_group, 'InvalidGroup.NotFound', 'DependencyViolation',
                                 GroupId=resource_id)
    # Eine erfolgreiche Löschanforderung ist noch keine bestätigte Abwesenheit.
    return result


def _request_removal(action, *retry_codes, **arguments):
    try:
        action(**arguments)
    except ClientError as error:
        if error.response['Error']['Code'] not in retry_codes:
            raise


def create_server(profile, region, timeout, account_id=None, network=None):
    server = MCPServer('diplomarbeit-aws', version='0.1', log_level='WARNING')

    def query(action, *, mutation=False):
        try:
            if mutation and (account_id is None or not os.environ.get(GUARD_TOKEN)):
                raise AdapterError('resource_conflict')
            with adapter_guard():
                session = boto3.Session(profile_name=profile, region_name=region)
                config = Config(connect_timeout=timeout, read_timeout=timeout,
                                retries={'total_max_attempts': 1})
                if account_id and session.client('sts', config=config).get_caller_identity()['Account'] != account_id:
                    raise AdapterError('resource_conflict')
                result = action(session.client('ec2', config=config))
        except AdapterError as error:
            result = {'ok': False, 'error': error.code}
        except ProcessGuardError:
            result = {'ok': False, 'error': 'resource_conflict'}
        except (ConnectTimeoutError, ReadTimeoutError):
            result = {'ok': False, 'error': 'timeout'}
        except (BotoCoreError, ClientError, OSError):
            result = {'ok': False, 'error': 'aws_query_failed'}
        except (KeyError, TypeError, ValueError):
            result = {'ok': False, 'error': 'invalid_response'}
        return CallToolResult(content=[], structured_content=result)

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def platform_status() -> CallToolResult:
        """Den EC2-Zustand der für den Agenten gekennzeichneten Instanzen lesen."""
        def read(client):
            instances = [{'id': item['InstanceId'], 'state': item['State']['Name']}
                         for item in _instances(client, _tag_filters())]
            result = {'ok': True, 'status': {'platform': 'aws', 'region': region,
                                             'instances': instances}}
            read_status_response(result)
            return result

        return query(read)

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def process_guard() -> CallToolResult:
        """Teilnahme an der Prozesssitzung des Agenten bestätigen."""
        try:
            with adapter_guard():
                return CallToolResult(content=[], structured_content={'session': os.environ.get(GUARD_TOKEN)})
        except ProcessGuardError:
            return CallToolResult(content=[], is_error=True)

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def create(run_id: str, operation_id: str, model: dict) -> CallToolResult:
        """Die Sicherheitsgruppe und eine EC2-Instanz schrittweise bereitstellen."""
        if network is None:
            return CallToolResult(content=[], structured_content={'ok': False, 'error': 'aws_launch_unconfigured'})

        def provision(client):
            result = {'ok': True, 'data': _create_step(client, region, network, run_id, operation_id, model)}
            read_result(result, CREATE_SCHEMA)
            return result

        return query(provision, mutation=True)

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True))
    def delete(run_id: str, operation_id: str, model_hash: str, resources: list[dict]) -> CallToolResult:
        """Einen Abbauschritt für den bestätigten AWS-Lauf ausführen."""
        def remove(client):
            validate_id(operation_id)
            result = {'ok': True, 'data': _delete_step(client, region, run_id, model_hash, resources)}
            read_result(result, DELETE_SCHEMA)
            return result

        return query(remove, mutation=True)

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def status(run_id: str) -> CallToolResult:
        """Die EC2-Ressourcen eines Laufs lesen; HTTP-Bereitschaft prüft der Agent."""
        def read(client):
            result = {'ok': True, 'data': run_status(client, region, run_id)}
            read_result(result, RUN_STATUS_SCHEMA)
            return result

        return query(read)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--account-id', help='Erwartetes AWS-Konto für schreibende Operationen')
    parser.add_argument('--vpc-id', help='VPC für die Security Group des Laufs')
    parser.add_argument('--subnet-id', help='Subnetz für die EC2-Instanz')
    parser.add_argument('--http-source-cidr', help='Öffentliche IPv4 des Agenten als /32')
    parser.add_argument('--timeout-seconds', type=int, default=15)
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds muss positiv sein')
    if args.account_id is not None and not re.fullmatch(r'[0-9]{12}', args.account_id):
        parser.error('--account-id muss eine zwölfstellige AWS-Kontonummer sein')
    network = None
    if any((args.vpc_id, args.subnet_id, args.http_source_cidr)):
        if (not args.account_id or args.region != 'us-east-1'
                or not re.fullmatch(r'vpc-[0-9a-f]+', args.vpc_id or '')
                or not re.fullmatch(r'subnet-[0-9a-f]+', args.subnet_id or '')):
            parser.error('AWS-Start benötigt Konto, VPC und Subnetz in us-east-1')
        try:
            source = IPv4Network(args.http_source_cidr or '')
        except ValueError:
            parser.error('--http-source-cidr benötigt eine öffentliche IPv4 mit /32')
        if source.prefixlen != 32 or not source.is_global:
            parser.error('--http-source-cidr benötigt eine öffentliche IPv4 mit /32')
        network = (args.vpc_id, args.subnet_id, str(source))
    create_server(args.profile, args.region, args.timeout_seconds, args.account_id, network).run(transport='stdio')


if __name__ == '__main__':
    main()

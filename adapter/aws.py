"""EC2-Ressourcen über Boto3 und MCP verwalten."""
import argparse
from ipaddress import IPv4Address
import os
import re

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ConnectTimeoutError, ReadTimeoutError
from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.kubevirt_manifest import validate_id
from adapter.vertrag import AdapterError, DELETE_SCHEMA, RUN_STATUS_SCHEMA, read_result, read_status_response
from gemeinsam.prozessschutz import GUARD_TOKEN, ProcessGuardError, adapter_guard


MANAGED_BY = 'diplomarbeit-agent'
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


def _inventory(client, region, run_id, known=()):
    resources = {}
    for kind, (id_key, id_filter, _, _) in RESOURCE_TYPES.items():
        items = _resource_items(client, kind, _tag_filters(run_id))
        visible_ids = {item[id_key] for item in items}
        missing_ids = sorted({key[1] for key in known if key[0] == kind} - visible_ids)
        if missing_ids:
            items.extend(_resource_items(client, kind, [{'Name': id_filter, 'Values': missing_ids}]))
        for item in items:
            tag_key = 'TagSet' if kind == 'NetworkInterface' else 'Tags'
            tags = {tag['Key']: tag['Value'] for tag in item.get(tag_key, [])}
            digest = tags.get('ModelHash', '')
            if (tags.get('ManagedBy') != MANAGED_BY or tags.get('RunId') != run_id
                    or not re.fullmatch(r'[0-9a-f]{64}', digest)):
                raise AdapterError('resource_conflict')
            resource_id = item[id_key]
            resource = {'kind': kind, 'name': resource_id, 'resource_id': resource_id, 'scope': region}
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


def create_server(profile, region, timeout, account_id=None):
    server = MCPServer('diplomarbeit-aws', version='0.1', log_level='WARNING')

    def query(action, *, mutation=False):
        try:
            if mutation and (account_id is None or not os.environ.get(GUARD_TOKEN)):
                raise AdapterError('resource_conflict')
            with adapter_guard():
                session = boto3.Session(profile_name=profile, region_name=region)
                config = Config(connect_timeout=timeout, read_timeout=timeout,
                                retries={'total_max_attempts': 1})
                if mutation and session.client('sts', config=config).get_caller_identity()['Account'] != account_id:
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
    parser.add_argument('--timeout-seconds', type=int, default=15)
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds muss positiv sein')
    if args.account_id is not None and not re.fullmatch(r'[0-9]{12}', args.account_id):
        parser.error('--account-id muss eine zwölfstellige AWS-Kontonummer sein')
    create_server(args.profile, args.region, args.timeout_seconds, args.account_id).run(transport='stdio')


if __name__ == '__main__':
    main()

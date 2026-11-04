"""EC2-Bestand über Boto3 und MCP lesen."""
import argparse
from ipaddress import IPv4Address
import re

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ConnectTimeoutError, ReadTimeoutError
from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.kubevirt_manifest import validate_id
from adapter.vertrag import AdapterError, RUN_STATUS_SCHEMA, read_result, read_status_response


MANAGED_BY = 'diplomarbeit-agent'
INSTANCE_STATES = {
    'pending': 'Provisioning', 'running': 'Running', 'shutting-down': 'Terminating',
    'stopping': 'Stopping', 'stopped': 'Stopped',
}


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


def run_status(client, region, run_id):
    """Aktive Instanz und unabhängig davon alle markierten Nebenressourcen erfassen."""
    validate_id(run_id)
    filters = _tag_filters(run_id)
    instances = [item for item in _instances(client, filters)
                 if item['State']['Name'] != 'terminated']
    if len(instances) > 1:
        raise AdapterError('resource_conflict')
    resources = []
    model_hashes = set()
    groups = [
        ('EC2Instance', 'InstanceId', instances),
        ('EBSVolume', 'VolumeId', _describe(client, 'describe_volumes', 'Volumes', filters)),
        ('NetworkInterface', 'NetworkInterfaceId',
         _describe(client, 'describe_network_interfaces', 'NetworkInterfaces', filters)),
        ('SecurityGroup', 'GroupId',
         _describe(client, 'describe_security_groups', 'SecurityGroups', filters)),
    ]
    for kind, id_key, items in groups:
        for item in items:
            tag_key = 'TagSet' if kind == 'NetworkInterface' else 'Tags'
            tags = {tag['Key']: tag['Value'] for tag in item.get(tag_key, [])}
            digest = tags.get('ModelHash', '')
            if (tags.get('ManagedBy') != MANAGED_BY or tags.get('RunId') != run_id
                    or not re.fullmatch(r'[0-9a-f]{64}', digest)):
                raise AdapterError('resource_conflict')
            model_hashes.add(digest)
            resource_id = item[id_key]
            resources.append({'kind': kind, 'name': resource_id, 'resource_id': resource_id,
                              'scope': region})
    if len(model_hashes) > 1:
        raise AdapterError('resource_conflict')

    instance = instances[0] if instances else {}
    state = INSTANCE_STATES[instance['State']['Name']] if instance else 'Absent'
    ready = state == 'Running'
    ip = instance.get('PublicIpAddress')
    http_url = f'http://{IPv4Address(ip)}:8080/' if ready and ip else None
    return {'resources': resources, 'vmState': state, 'vmiPhase': state, 'vmReady': ready,
            'modelHash': next(iter(model_hashes), None), 'httpUrl': http_url,
            'sshHost': None, 'sshPort': None}


def create_server(profile, region, timeout):
    server = MCPServer('diplomarbeit-aws', version='0.1', log_level='WARNING')

    def query(action):
        try:
            client = boto3.Session(profile_name=profile, region_name=region).client(
                'ec2', config=Config(connect_timeout=timeout, read_timeout=timeout,
                                     retries={'total_max_attempts': 1}),
            )
            result = action(client)
        except AdapterError as error:
            result = {'ok': False, 'error': error.code}
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
    parser.add_argument('--timeout-seconds', type=int, default=15)
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds muss positiv sein')
    create_server(args.profile, args.region, args.timeout_seconds).run(transport='stdio')


if __name__ == '__main__':
    main()

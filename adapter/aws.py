"""EC2-Bestand über Boto3 und MCP lesen."""
import argparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ConnectTimeoutError, ReadTimeoutError
from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.vertrag import read_status_response


def create_server(profile, region, timeout):
    server = MCPServer('diplomarbeit-aws', version='0.1', log_level='WARNING')

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def platform_status() -> CallToolResult:
        """Den EC2-Zustand der für den Agenten gekennzeichneten Instanzen lesen."""
        try:
            client = boto3.Session(profile_name=profile, region_name=region).client(
                'ec2', config=Config(connect_timeout=timeout, read_timeout=timeout,
                                     retries={'total_max_attempts': 1}),
            )
            pages = client.get_paginator('describe_instances').paginate(
                Filters=[{'Name': 'tag:ManagedBy', 'Values': ['diplomarbeit-agent']}],
            )
            instances = [
                {'id': instance['InstanceId'], 'state': instance['State']['Name']}
                for page in pages
                for reservation in page['Reservations']
                for instance in reservation['Instances']
            ]
            result = {'ok': True, 'status': {'platform': 'aws', 'region': region,
                                             'instances': instances}}
            read_status_response(result)
        except (ConnectTimeoutError, ReadTimeoutError):
            result = {'ok': False, 'error': 'timeout'}
        except (BotoCoreError, ClientError, OSError):
            result = {'ok': False, 'error': 'aws_query_failed'}
        except (KeyError, TypeError, ValueError):
            result = {'ok': False, 'error': 'invalid_response'}
        return CallToolResult(content=[], structured_content=result)

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

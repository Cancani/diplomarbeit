"""EC2-Bestand über AWS CLI und MCP lesen."""
import argparse
import json
import subprocess

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.vertrag import AdapterError, read_status_response


def create_server(command, profile, region, timeout):
    server = MCPServer('diplomarbeit-aws', version='0.1', log_level='WARNING')

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
    def platform_status() -> CallToolResult:
        """Den EC2-Zustand der für den Agenten gekennzeichneten Instanzen lesen."""
        try:
            response = subprocess.run(
                [*command, 'ec2', 'describe-instances', '--profile', profile, '--region', region,
                 '--filters', 'Name=tag:ManagedBy,Values=diplomarbeit-agent',
                 '--query', 'Reservations[].Instances[].{id:InstanceId,state:State.Name}',
                 '--output', 'json', '--no-cli-pager', '--no-cli-auto-prompt'],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8',
                timeout=timeout, check=True,
            )
            result = {'ok': True, 'status': {'platform': 'aws', 'region': region,
                                             'instances': json.loads(response.stdout)}}
            read_status_response(result)
        except FileNotFoundError:
            result = {'ok': False, 'error': 'aws_cli_unavailable'}
        except subprocess.TimeoutExpired:
            result = {'ok': False, 'error': 'timeout'}
        except (subprocess.CalledProcessError, OSError):
            result = {'ok': False, 'error': 'aws_query_failed'}
        except ValueError:
            result = {'ok': False, 'error': 'invalid_response'}
        return CallToolResult(content=[], structured_content=result)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aws-command', nargs='+', default=['aws'])
    parser.add_argument('--profile', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--timeout-seconds', type=int, default=15)
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds muss positiv sein')
    create_server(args.aws_command, args.profile, args.region, args.timeout_seconds).run(transport='stdio')


if __name__ == '__main__':
    main()

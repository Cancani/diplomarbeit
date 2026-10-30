"""KubeVirt-Abfragen als MCP-Werkzeug über stdio anbieten."""
import argparse

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.kubevirt_provider import KubeVirtProvider
from adapter.vertrag import AdapterError, read_status_response


def create_server(provider):
    server = MCPServer('diplomarbeit-kubevirt', version='0.1', log_level='WARNING')

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    def platform_status() -> CallToolResult:
        """Knoten, KubeVirt und VMs lesen; keine Dienstbereitschaft bestätigen."""
        try:
            response = {'ok': True, 'status': provider.platform_status()}
            read_status_response(response)
        except AdapterError as error:
            response = {'ok': False, 'error': error.code}
        return CallToolResult(content=[], structured_content=response)

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kubectl-command', nargs='+', default=['microk8s', 'kubectl'],
                        help='Programm und feste Argumente für kubectl')
    parser.add_argument('--timeout-seconds', type=int, default=15,
                        help='Gesamte Zeitgrenze für die Kubernetes-Abfragen')
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error('--timeout-seconds muss positiv sein')
    create_server(KubeVirtProvider(args.kubectl_command, args.timeout_seconds)).run(transport='stdio')


if __name__ == '__main__':
    main()

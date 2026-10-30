"""KubeVirt-Abfragen als MCP-Werkzeug über stdio anbieten."""
import argparse

from mcp.server import MCPServer
from mcp.types import CallToolResult, ToolAnnotations

from adapter.kubevirt_lifecycle import KubeVirtLifecycle
from adapter.vertrag import AdapterError, read_status_response
from modell.validierung import ModelValidationError


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

    def result(action):
        try:
            response = {'ok': True, 'data': action()}
        except AdapterError as error:
            response = {'ok': False, 'error': error.code}
        except ModelValidationError:
            response = {'ok': False, 'error': 'invalid_request'}
        return CallToolResult(content=[], structured_content=response)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
    def create(run_id: str, operation_id: str, model: dict) -> CallToolResult:
        """Einen Erstellungsschritt bestätigen; complete meldet VM und Service als angelegt."""
        return result(lambda: provider.create(run_id, operation_id, model))

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    def status(run_id: str) -> CallToolResult:
        """Ressourcen und VM-Zustand lesen; HTTP-Prüfung erfolgt durch den Agenten."""
        return result(lambda: provider.status(run_id))

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    def delete(run_id: str, operation_id: str, resources: list[dict]) -> CallToolResult:
        """Einen Abbauschritt ausführen und bestätigte Ressourcenabwesenheit zurückgeben."""
        return result(lambda: provider.delete(run_id, operation_id, resources))

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
    create_server(KubeVirtLifecycle(args.kubectl_command, args.timeout_seconds)).run(transport='stdio')


if __name__ == '__main__':
    main()

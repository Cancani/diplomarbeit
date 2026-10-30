"""Testserver für echte stdio-Kommunikation ohne Cluster."""
from pathlib import Path
import sys
import time


mode = sys.argv[1]
if mode == 'silent':
    # Noch vor dem SDK-Import: Ein Prozess ohne MCP-Handshake muss beendet werden.
    heartbeat = Path(sys.argv[2])
    counter = 0
    while True:
        heartbeat.write_text(str(counter), encoding='utf-8')
        counter += 1
        time.sleep(0.05)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mcp.server import MCPServer
from mcp.types import CallToolResult

from adapter.kubevirt import create_server
from adapter.vertrag import AdapterError


class FakeProvider:
    def platform_status(self):
        if mode == 'error':
            raise AdapterError('platform_error')
        return {
            'platform': 'kubevirt', 'nodes': [{'name': 'test-node', 'ready': True}],
            'kubevirtPhase': 'Deployed', 'virtualMachines': [], 'virtualMachineInstances': [],
        }

    def create(self, run_id, operation_id, model):
        return {'complete': True, 'resources': [
            {'kind': 'VirtualMachine', 'name': 'test-vm', 'scope': 'test', 'resource_id': 'test-uid'}]}

    def status(self, run_id):
        return {'resources': [], 'vmState': 'Absent', 'vmiPhase': 'Absent', 'vmReady': False,
                'modelHash': None, 'httpUrl': None, 'sshHost': None, 'sshPort': None}

    def delete(self, run_id, operation_id, resources):
        return {'complete': True, 'resources': [], 'removed': resources}


if mode == 'invalid':
    server = MCPServer('test-invalid-adapter', log_level='WARNING')

    @server.tool()
    def platform_status() -> CallToolResult:
        return CallToolResult(content=[], structured_content={'unexpected': 'PRIVATE-CONTENT'})
else:
    server = create_server(FakeProvider())


server.run(transport='stdio')

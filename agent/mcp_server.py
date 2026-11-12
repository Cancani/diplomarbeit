"""Nur-Lese-Status einer Lernumgebung als MCP-Werkzeug über stdio anbieten."""
import argparse
import json
import sqlite3

import anyio
from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from adapter.vertrag import AdapterError
from agent.dashboard import read_runs
from agent.konfiguration import ConfigurationError, load_config
from agent.lebenszyklus import inspect_status
from agent.zustand import StateError


def read_status(config, run_id):
    """Gespeicherten Lauf lesen und Plattform sowie HTTP-Dienst prüfen."""
    try:
        run = next((run for run in read_runs(config['stateFile']) if run['run_id'] == run_id), None)
    except sqlite3.Error:
        return {'ok': False, 'runId': run_id, 'error': 'Der Zustandsspeicher ist momentan nicht lesbar.'}
    if run is None:
        return {'ok': False, 'runId': run_id,
                'error': 'Für diese Laufkennung ist keine Umgebung gespeichert.'}
    try:
        run['model_snapshot'] = json.loads(run['model_snapshot'])
        actual, ready = inspect_status(config, run)
    except (AdapterError, StateError) as error:
        return {'ok': False, 'runId': run_id, 'error': str(error)}
    except ValueError:
        return {'ok': False, 'runId': run_id, 'error': 'Der gespeicherte Lauf ist nicht lesbar.'}
    return {'ok': True, 'runId': run_id, 'platform': run['platform'], 'storedPhase': run['phase'],
            'vmState': actual['vmState'], 'vmiPhase': actual['vmiPhase'], 'vmReady': actual['vmReady'],
            'httpReady': ready, 'httpUrl': actual['httpUrl']}


def create_server(config):
    server = MCPServer('diplomarbeit-lernumgebung', version='0.1', log_level='WARNING')

    @server.tool(annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False))
    async def lernumgebung_status(run_id: str) -> CallToolResult:
        """VM-Status und HTTP-Bereitschaft einer gespeicherten Lernumgebung live prüfen.

        run_id ist die Laufkennung, zum Beispiel s2-kv-01. Die Abfrage ändert nichts.
        httpReady ist nur wahr, wenn die VM läuft und der HTTP-Testdienst wie erwartet antwortet.
        """
        # Die Statusprüfung startet eigene Ereignisschleifen und darf diese hier nicht blockieren.
        response = await anyio.to_thread.run_sync(read_status, config, run_id)
        text = json.dumps(response, ensure_ascii=False)
        return CallToolResult(content=[TextContent(type='text', text=text)],
                              structured_content=response, is_error=not response['ok'])

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, help='Pfad zur Agent-Konfiguration')
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigurationError as error:
        parser.exit(1, f'{error}\n')
    create_server(config).run(transport='stdio')


if __name__ == '__main__':
    main()

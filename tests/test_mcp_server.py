import asyncio
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import Client, StdioServerParameters
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.zustand import StateStore
from modell.validierung import load_model


class McpServerTests(unittest.TestCase):
    def call(self, folder, run_id):
        """Server als eigenen Prozess starten und über echtes stdio abfragen."""
        async def session():
            parameters = StdioServerParameters(
                command=sys.executable,
                args=['-m', 'agent.mcp_server', '--config', str(Path(folder)/'config.yaml')],
                cwd=ROOT, env={'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
            async with Client(parameters, read_timeout_seconds=30) as client:
                tools = (await client.list_tools()).tools
                return tools, await client.call_tool('lernumgebung_status', {'run_id': run_id})
        return asyncio.run(asyncio.wait_for(session(), 60))

    def prepare(self, folder):
        (Path(folder)/'config.yaml').write_text(yaml.safe_dump({
            'stateFile': 'zustand.sqlite3', 'adapters': {'kubevirt': {
                'command': sys.executable,
                'args': [str(ROOT/'tests/fixtures/mcp_adapter.py'), 'ok'], 'timeoutSeconds': 10}},
        }), encoding='utf-8')
        state = Path(folder)/'zustand.sqlite3'
        StateStore(state).start_create('lokal-01', 'op-01', 'kubevirt',
                                       load_model(ROOT/'modell/beispiele/referenz.yaml'))
        return state

    def test_single_read_only_tool_reports_vm_and_http_state(self):
        with tempfile.TemporaryDirectory() as folder:
            state = self.prepare(folder)
            before = state.read_bytes()
            tools, result = self.call(folder, 'lokal-01')
            self.assertEqual(state.read_bytes(), before)
        self.assertEqual([tool.name for tool in tools], ['lernumgebung_status'])
        self.assertTrue(tools[0].annotations.read_only_hint)
        self.assertFalse(result.is_error)
        self.assertEqual(result.structured_content, {
            'ok': True, 'runId': 'lokal-01', 'platform': 'kubevirt', 'storedPhase': 'creating',
            'vmState': 'Absent', 'vmiPhase': 'Absent', 'vmReady': False,
            'httpReady': False, 'httpUrl': None})
        self.assertIn('"httpReady": false', result.content[0].text)

    def test_unknown_run_is_reported_without_creating_state(self):
        with tempfile.TemporaryDirectory() as folder:
            self.prepare(folder)
            _, result = self.call(folder, 'unbekannt-99')
            self.assertEqual(sorted(path.name for path in Path(folder).iterdir()),
                             ['config.yaml', 'zustand.sqlite3'])
        self.assertTrue(result.is_error)
        self.assertEqual(result.structured_content['runId'], 'unbekannt-99')
        self.assertIn('keine Umgebung gespeichert', result.structured_content['error'])


if __name__ == '__main__':
    unittest.main()

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.zustand import StateStore
from modell.validierung import load_model


class AgentCliTests(unittest.TestCase):
    def invoke(self, arguments, config=ROOT/'agent/beispiele/konfiguration.yaml'):
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='cp1252')
        config_args = [] if config is None else ['--config', str(config)]
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, '-m', 'agent', *config_args, *arguments],
                                    cwd=folder, env=env, capture_output=True,
                                    text=True, encoding='utf-8', timeout=15)
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertNotIn('Traceback', result.stderr)
        return result

    def test_help_for_all_commands(self):
        for command in [[], ['create'], ['status'], ['reset'], ['delete'], ['platform-status']]:
            with self.subTest(command=command):
                result = self.invoke([*command, '--help'], config=None)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(result.stdout)
                self.assertEqual(result.stderr, '')

    def test_missing_and_unknown_arguments(self):
        for arguments in [[], ['unknown'], ['status'], ['platform-status'],
                          ['reset', '--run-id', 'lokal-01', '--timeout-seconds', '0'],
                          ['create', 'definition.yaml', '--run-id', 'lokal-01',
                           '--platform', 'unknown']]:
            with self.subTest(arguments=arguments):
                result = self.invoke(arguments)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)

    def test_invalid_model_rejected(self):
        for name, message in [('ungueltig-ram.yaml', '$.vm.resources.minMemoryMiB'),
                              ('missing.yaml', 'Datei konnte nicht gelesen werden')]:
            with self.subTest(name=name):
                result = self.invoke(['create', str(ROOT/'modell/beispiele'/name),
                                      '--platform', 'kubevirt', '--run-id', 'lokal-01'])
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertNotIn('noch nicht implementiert', result.stderr)

    def test_valid_create_reports_adapter_start_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder)/'config.yaml'
            config.write_text(yaml.safe_dump({
                'stateFile': 'zustand.sqlite3', 'adapters': {'kubevirt': {
                    'command': str(Path(folder)/'missing-adapter'), 'args': [], 'timeoutSeconds': 1}},
            }), encoding='utf-8')
            result = self.invoke(['create', str(ROOT/'modell/beispiele/referenz.yaml'),
                                  '--platform', 'kubevirt', '--run-id', 'lokal-01'], config=config)
        self.assertEqual(result.returncode, 1)
        self.assertIn('MCP-Adapter', result.stderr)
        self.assertIn('Lernumgebung wird erstellt.', result.stdout)
        self.assertIn('Bekannte Ressourcen zur weiteren Prüfung:', result.stdout)
        self.assertNotIn('resource_id', result.stdout)

    def test_json_option_works_before_and_after_the_command_and_keeps_error_events(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root/'config.yaml'
            config.write_text(yaml.safe_dump({
                'stateFile': 'state.sqlite3', 'adapters': {'kubevirt': {
                    'command': str(root/'missing-adapter'), 'args': [], 'timeoutSeconds': 1}},
            }), encoding='utf-8')
            for index, before in enumerate((True, False)):
                arguments = ['create', str(ROOT/'modell/beispiele/referenz.yaml'),
                             '--platform', 'kubevirt', '--run-id', f'json-{index}',
                             '--operation-id', f'create-json-{index}']
                arguments = ['--json', *arguments] if before else [*arguments, '--json']
                with self.subTest(before_command=before):
                    result = self.invoke(arguments, config=config)
                    self.assertEqual(result.returncode, 1)
                    events = [json.loads(line) for line in result.stdout.splitlines()]
                    self.assertEqual([e['event'] for e in events], ['create_started', 'error'])
                    self.assertEqual(events[-1]['operationId'], f'create-json-{index}')
                    self.assertIn('timeUtc', events[-1])
                    self.assertEqual(events[-1]['resources'], [])

    def test_status_is_readable_by_default_and_json_is_explicit_over_real_stdio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root/'config.yaml'
            config.write_text(yaml.safe_dump({
                'stateFile': 'state.sqlite3', 'adapters': {'kubevirt': {
                    'command': sys.executable, 'timeoutSeconds': 10,
                    'args': [str(ROOT/'tests/fixtures/mcp_adapter.py'), 'success']}},
            }), encoding='utf-8')
            store = StateStore(root/'state.sqlite3')
            store.start_create('readable-01', 'create-readable-01', 'kubevirt',
                               load_model(ROOT/'modell/beispiele/referenz.yaml'))
            store.record_resource('readable-01', 'create-readable-01', 'VirtualMachine', 'known-uid')
            store.fail('readable-01', 'create-readable-01', 'timeout')
            result = self.invoke(['status', '--run-id', 'readable-01'], config=config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Gespeicherter Zustand: Fehler', result.stdout)
            self.assertIn('VM: Nicht vorhanden', result.stdout)
            self.assertIn('HTTP-Dienst: Nicht bestätigt', result.stdout)
            self.assertIn('Aktuell beobachtete Ressourcen: 0', result.stdout)
            self.assertNotIn('known-uid', result.stdout)
            result = self.invoke(['status', '--run-id', 'readable-01', '--json'], config=config)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data['event'], 'status')
            self.assertEqual(data['storedPhase'], 'error')
            self.assertFalse(data['serviceReady'])
            self.assertEqual(data['resources'], [])
            self.assertEqual(store.get('readable-01')['resources'][0]['resource_id'], 'known-uid')

    def test_existing_run_operations_require_a_stored_environment(self):
        for operation in ['status', 'reset', 'delete']:
            with self.subTest(operation=operation):
                arguments = [operation, '--run-id', 'lokal-01']
                if operation == 'reset':
                    arguments += ['--operation-id', 'reset-01', '--timeout-seconds', '1200']
                result = self.invoke(arguments)
                self.assertEqual(result.returncode, 1)
                self.assertIn('keine Umgebung gespeichert', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_config_option_is_required(self):
        result = self.invoke(['status', '--run-id', 'lokal-01'], config=None)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--config', result.stderr)

    def test_missing_config_file(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.invoke(['status', '--run-id', 'lokal-01'],
                                 config=Path(folder)/'missing.yaml')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Konfigurationsfehler:', result.stderr)
        self.assertIn('nicht gelesen', result.stderr)

    def test_invalid_config_does_not_echo_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'invalid.yaml'
            path.write_text('stateFile: PRIVATE-CONTENT\nadapters: []\n', encoding='utf-8')
            result = self.invoke(['status', '--run-id', 'lokal-01'], config=path)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Konfigurationsfehler:', result.stderr)
        self.assertNotIn('PRIVATE-CONTENT', result.stderr)

    def test_unconfigured_platform_rejected(self):
        result = self.invoke(['create', str(ROOT/'modell/beispiele/referenz.yaml'),
                              '--platform', 'aws', '--run-id', 'cloud-01'])
        self.assertEqual(result.returncode, 1)
        self.assertIn('kein Adapter konfiguriert', result.stderr)


if __name__ == '__main__':
    unittest.main()

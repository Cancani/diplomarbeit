from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.cli import build_parser, run
from agent.konfiguration import ConfigurationError, default_config_path
from agent.zustand import StateStore
from modell.validierung import load_model


class DefaultConfigTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.source = self.root/'config.yaml'
        self.state = self.root/'state.sqlite3'
        adapter = {'command': sys.executable, 'args': [], 'timeoutSeconds': 5}
        self.source.write_text(yaml.safe_dump({
            'stateFile': str(self.state),
            'adapters': {'kubevirt': adapter, 'aws': {**adapter, 'args': []}},
        }), encoding='utf-8')
        self.model_path = ROOT/'modell/beispiele/referenz.yaml'

    def invoke(self, arguments):
        stderr = StringIO()
        with redirect_stdout(StringIO()), redirect_stderr(stderr):
            result = run(build_parser().parse_args(arguments))
        return result, stderr.getvalue()

    def test_platform_defaults_are_independent_of_the_working_directory(self):
        self.assertEqual(default_config_path('kubevirt'),
                         ROOT/'agent/beispiele/konfiguration.yaml')
        self.assertEqual(default_config_path('aws'),
                         Path.home()/'.config/diplomarbeit/aws.yaml')
        with self.assertRaises(ConfigurationError):
            default_config_path(None)

    def test_create_uses_the_selected_platform_default(self):
        for platform in ('kubevirt', 'aws'):
            with self.subTest(platform=platform), \
                    patch('agent.cli.default_config_path', return_value=self.source) as select, \
                    patch('agent.lebenszyklus.create') as create:
                result, error = self.invoke([
                    'create', str(self.model_path), '--platform', platform,
                    '--run-id', 'default-01', '--operation-id', 'create-default-01',
                ])
                self.assertEqual((result, error), (0, ''))
                select.assert_called_once_with(platform)
                self.assertEqual(create.call_args.args[0]['stateFile'], self.state)
                self.assertEqual(create.call_args.args[3], platform)
                self.assertFalse(self.state.exists())

    def test_explicit_config_has_priority(self):
        with patch('agent.cli.default_config_path') as select, \
                patch('agent.lebenszyklus.create') as create:
            result, error = self.invoke([
                '--config', str(self.source), 'create', str(self.model_path),
                '--platform', 'aws', '--run-id', 'explicit-01',
            ])
        self.assertEqual((result, error), (0, ''))
        select.assert_not_called()
        self.assertEqual(create.call_args.args[0]['stateFile'], self.state)

    def test_platform_status_uses_the_selected_default(self):
        for platform in ('kubevirt', 'aws'):
            response = {'status': {'platform': platform}}
            with self.subTest(platform=platform), \
                    patch('agent.cli.default_config_path', return_value=self.source) as select, \
                    patch('agent.mcp_client.platform_status', return_value=response) as status, \
                    patch('agent.cli.platform_result') as output:
                result, error = self.invoke(['platform-status', '--platform', platform])
                self.assertEqual((result, error), (0, ''))
                select.assert_called_once_with(platform)
                status.assert_called_once()
                output.assert_called_once_with(response, False)
        self.assertFalse(self.state.exists())

    def test_missing_default_reports_the_path_without_creating_a_database(self):
        missing = self.root/'not-configured/aws.yaml'
        with patch('agent.cli.default_config_path', return_value=missing):
            result, error = self.invoke([
                'create', str(self.model_path), '--platform', 'aws', '--run-id', 'missing-01',
            ])
        self.assertEqual(result, 1)
        self.assertIn(str(missing), error)
        self.assertIn('--config', error)
        self.assertFalse(missing.parent.exists())
        self.assertFalse(self.state.exists())

    def test_existing_run_operations_accept_a_matching_platform(self):
        store = StateStore(self.state)
        model = load_model(self.model_path)
        for platform in ('kubevirt', 'aws'):
            run_id = f'{platform}-01'
            store.start_create(run_id, f'create-{run_id}', platform, model)
            for operation in ('status', 'reset', 'delete'):
                with self.subTest(platform=platform, operation=operation), \
                        patch('agent.cli.default_config_path', return_value=self.source) as select, \
                        patch(f'agent.lebenszyklus.{operation}') as command:
                    result, error = self.invoke([
                        operation, '--platform', platform, '--run-id', run_id,
                    ])
                    self.assertEqual((result, error), (0, ''))
                    select.assert_called_once_with(platform)
                    command.assert_called_once()
                    self.assertEqual(command.call_args.args[1], run_id)

    def test_wrong_platform_stops_before_the_lifecycle_operation(self):
        store = StateStore(self.state)
        store.start_create('cloud-01', 'create-cloud-01', 'aws', load_model(self.model_path))
        for operation in ('status', 'reset', 'delete'):
            with self.subTest(operation=operation), \
                    patch(f'agent.lebenszyklus.{operation}') as command:
                result, error = self.invoke([
                    '--config', str(self.source), operation, '--platform', 'kubevirt',
                    '--run-id', 'cloud-01',
                ])
                self.assertEqual(result, 1)
                self.assertIn('Plattform passt nicht', error)
                command.assert_not_called()
        self.assertEqual(store.get('cloud-01')['phase'], 'creating')

    def test_reading_an_unknown_run_does_not_create_a_database(self):
        with patch('agent.cli.default_config_path', return_value=self.source):
            result, error = self.invoke(['status', '--platform', 'aws', '--run-id', 'missing-01'])
        self.assertEqual(result, 1)
        self.assertIn('keine Umgebung gespeichert', error)
        self.assertFalse(self.state.exists())


if __name__ == '__main__':
    unittest.main()

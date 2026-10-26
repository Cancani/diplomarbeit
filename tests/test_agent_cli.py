import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentCliTests(unittest.TestCase):
    def invoke(self, arguments):
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='cp1252')
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, '-m', 'agent', *arguments],
                                    cwd=folder, env=env, capture_output=True,
                                    text=True, encoding='utf-8', timeout=15)
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertNotIn('Traceback', result.stderr)
        return result

    def test_help_for_all_commands(self):
        for command in [[], ['create'], ['status'], ['reset'], ['delete']]:
            with self.subTest(command=command):
                result = self.invoke([*command, '--help'])
                self.assertEqual(result.returncode, 0)
                self.assertTrue(result.stdout)
                self.assertEqual(result.stderr, '')

    def test_missing_and_unknown_arguments(self):
        for arguments in [[], ['unknown'], ['status'],
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

    def test_valid_create_reports_missing_lifecycle(self):
        result = self.invoke(['create', str(ROOT/'modell/beispiele/referenz.yaml'),
                              '--platform', 'kubevirt', '--run-id', 'lokal-01'])
        self.assertEqual(result.returncode, 1)
        self.assertIn('Lebenszyklussteuerung ist noch nicht implementiert', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_existing_run_operations_report_missing_lifecycle(self):
        for operation in ['status', 'reset', 'delete']:
            with self.subTest(operation=operation):
                result = self.invoke([operation, '--run-id', 'lokal-01'])
                self.assertEqual(result.returncode, 1)
                self.assertIn('Lebenszyklussteuerung ist noch nicht implementiert', result.stderr)
                self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modell.validierung import load_model, validate_model, ModelValidationError, SCHEMA_PATH


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.reference = load_model(ROOT/'modell/beispiele/referenz.yaml')

    def test_schema_and_complete_reference(self):
        Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text(encoding='utf-8')))
        self.assertEqual(self.reference['modelVersion'], '1.0')
        self.assertEqual(self.reference['vm']['resources'],
                         {'minVcpus': 2, 'minMemoryMiB': 2048, 'minDiskGiB': 12})
        self.assertEqual(self.reference['vm']['testService']['expectedBody'], 'lernumgebung bereit')

    def test_versioned_negative_example_has_specific_error(self):
        with self.assertRaises(ModelValidationError) as caught:
            load_model(ROOT/'modell/beispiele/ungueltig-ram.yaml')
        self.assertEqual(caught.exception.errors,
                         ('$.vm.resources.minMemoryMiB: Muss mindestens 2048 sein.',))

    def test_resource_boundaries_and_types(self):
        for field, minimum in [('minVcpus', 2), ('minMemoryMiB', 2048), ('minDiskGiB', 12)]:
            for value in [minimum - 1, str(minimum), True, 2.5]:
                with self.subTest(field=field, value=value), self.assertRaises(ModelValidationError):
                    model = deepcopy(self.reference)
                    model['vm']['resources'][field] = value
                    validate_model(model)
            model = deepcopy(self.reference)
            model['vm']['resources'][field] = minimum * 2
            self.assertEqual(validate_model(model), model)

    def test_platform_fields_rejected_at_multiple_levels(self):
        for path, field in [((), 'provider'), (('vm',), 'amiId'),
                            (('vm', 'resources'), 'storageClass'),
                            (('vm', 'testService'), 'nodePort')]:
            with self.subTest(field=field), self.assertRaises(ModelValidationError):
                model = deepcopy(self.reference)
                target = model
                for step in path:
                    target = target[step]
                target[field] = 'not-part-of-the-model'
                validate_model(model)

    def test_required_fields_and_unknown_version(self):
        for field in ['role', 'os', 'resources', 'ssh', 'testService']:
            with self.subTest(field=field), self.assertRaises(ModelValidationError):
                model = deepcopy(self.reference)
                del model['vm'][field]
                validate_model(model)
        model = deepcopy(self.reference)
        model['modelVersion'] = '2.0'
        with self.assertRaises(ModelValidationError):
            validate_model(model)

    def test_fixed_workload_and_names(self):
        for path, value in [(('name',), '../wrong'), (('name',), 'bad\n'),
                            (('vm', 'role'), 'desktop'),
                            (('vm', 'os', 'release'), '22.04'),
                            (('vm', 'os', 'architecture'), 'arm64'),
                            (('vm', 'testService', 'expectedStatus'), 404),
                            (('vm', 'testService', 'port'), 80),
                            (('vm', 'testService', 'expectedBody'), 'wrong')]:
            with self.subTest(path=path), self.assertRaises(ModelValidationError):
                model = deepcopy(self.reference)
                target = model
                for step in path[:-1]:
                    target = target[step]
                target[path[-1]] = value
                validate_model(model)

    def test_ssh_key_structure_and_no_secret_in_error(self):
        secret = '-----BEGIN OPENSSH PRIVATE KEY-----\nPRIVATE-CONTENT'
        key = self.reference['vm']['ssh']['publicKeys'][0]
        for keys in [[], [key, key], ['ssh-ed25519 ' + 'A' * 68], [secret]]:
            with self.subTest(keys=keys), self.assertRaises(ModelValidationError) as caught:
                model = deepcopy(self.reference)
                model['vm']['ssh']['publicKeys'] = keys
                validate_model(model)
            self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))

    def test_yaml_errors_are_clear_and_do_not_echo_values(self):
        cases = [
            ('name: a\nname: b\n', 'Doppeltes YAML-Feld'),
            ('vm:\n  role: server\n  role: desktop\n', 'Doppeltes YAML-Feld'),
            ('a: &a [*a]\n', 'YAML-Aliase'),
            ('true: value\n', 'Feldnamen'),
            ('---\nname: a\n---\nname: b\n', 'Ungueltiges YAML'),
            ('vm: [PRIVATE-CONTENT', 'Ungueltiges YAML'),
            ('name: !!python/object:example {}', 'Ungueltiges YAML'),
            ('name: 2026-09-23\n', 'JSON-kompatible'),
            ('vm: .nan\n', 'JSON-kompatible'),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'input.yaml'
            for text, expected in cases:
                with self.subTest(expected=expected):
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaises(ModelValidationError) as caught:
                        load_model(path)
                    self.assertIn(expected, str(caught.exception))
                    self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))

    def test_empty_document_and_wrong_top_level(self):
        for value in [None, [], 'text', 123, True]:
            with self.subTest(value=value), self.assertRaises(ModelValidationError):
                validate_model(value)

    def test_cli_from_other_directory_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            for file, code, message in [('referenz.yaml', 0, 'Gueltig: referenzumgebung'),
                                        ('ungueltig-ram.yaml', 1, '$.vm.resources.minMemoryMiB'),
                                        ('missing.yaml', 1, 'Datei konnte nicht gelesen werden')]:
                with self.subTest(file=file):
                    result = subprocess.run([sys.executable, str(ROOT/'scripts/modell-pruefen.py'),
                                             str(ROOT/'modell/beispiele'/file)], cwd=folder,
                                            text=True, encoding='utf-8', capture_output=True)
                    self.assertEqual(result.returncode, code)
                    self.assertIn(message, result.stdout if code == 0 else result.stderr)
                    self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()

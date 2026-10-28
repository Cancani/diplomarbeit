from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.konfiguration import ConfigurationError, load_config


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        self.source = self.root/'agent.yaml'
        self.reference = {
            'stateFile': 'state/zustand.sqlite3',
            'adapters': {'kubevirt': {
                'command': 'python', 'args': ['-m', 'adapter.kubevirt'], 'timeoutSeconds': 30}},
        }

    def write(self, document):
        self.source.write_text(yaml.safe_dump(document), encoding='utf-8')
        return load_config(self.source)

    def test_valid_config_resolves_relative_state_path_without_creating_it(self):
        config = self.write(self.reference)
        self.assertEqual(config['stateFile'], self.root/'state/zustand.sqlite3')
        self.assertEqual(config['adapters'], self.reference['adapters'])
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_absolute_and_home_state_paths(self):
        for value, expected in [(str(self.root/'absolute.sqlite3'), self.root/'absolute.sqlite3'),
                                ('~/diplomarbeit/zustand.sqlite3',
                                 Path.home()/'diplomarbeit/zustand.sqlite3')]:
            with self.subTest(value=value):
                document = deepcopy(self.reference)
                document['stateFile'] = value
                self.assertEqual(self.write(document)['stateFile'], expected.resolve())

    def test_missing_or_unreadable_file(self):
        for source in [self.root/'missing.yaml', self.root]:
            with self.subTest(source=source), self.assertRaises(ConfigurationError) as caught:
                load_config(source)
            self.assertIn('nicht gelesen', str(caught.exception))

    def test_invalid_encoding_and_yaml(self):
        self.source.write_bytes(b'stateFile: \xff')
        with self.assertRaises(ConfigurationError) as caught:
            load_config(self.source)
        self.assertIn('UTF-8', str(caught.exception))
        for content in ['stateFile: a\nstateFile: b\n', 'a: &a [*a]\n',
                        'true: value\n', '---\na: 1\n---\nb: 2\n', 'a: [PRIVATE-CONTENT']:
            with self.subTest(content=content), self.assertRaises(ConfigurationError) as caught:
                self.source.write_text(content, encoding='utf-8')
                load_config(self.source)
            self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))

    def test_required_and_unknown_fields(self):
        documents = [None, [], {}, {**self.reference, 'unknown': 'PRIVATE-CONTENT'}]
        for field in ['stateFile', 'adapters']:
            document = deepcopy(self.reference)
            del document[field]
            documents.append(document)
        for document in documents:
            with self.subTest(document=document), self.assertRaises(ConfigurationError) as caught:
                self.write(document)
            self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))

    def test_adapter_values_and_platforms(self):
        for field, values in [('command', ['', ' ', None, ['PRIVATE-CONTENT']]),
                              ('args', ['PRIVATE-CONTENT', [None], [1]]),
                              ('timeoutSeconds', [0, -1, True, 1.5, '30'])]:
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ConfigurationError) as caught:
                    document = deepcopy(self.reference)
                    document['adapters']['kubevirt'][field] = value
                    self.write(document)
                self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))
        for adapters in [{}, {'unknown': self.reference['adapters']['kubevirt']}]:
            with self.subTest(adapters=adapters), self.assertRaises(ConfigurationError):
                self.write({**self.reference, 'adapters': adapters})
        document = deepcopy(self.reference)
        document['adapters']['aws'] = document['adapters'].pop('kubevirt')
        self.assertIn('aws', self.write(document)['adapters'])

    def test_missing_and_unknown_adapter_fields(self):
        for field in ['command', 'args', 'timeoutSeconds']:
            with self.subTest(field=field), self.assertRaises(ConfigurationError):
                document = deepcopy(self.reference)
                del document['adapters']['kubevirt'][field]
                self.write(document)
        document = deepcopy(self.reference)
        document['adapters']['kubevirt']['secret'] = 'PRIVATE-CONTENT'
        with self.assertRaises(ConfigurationError) as caught:
            self.write(document)
        self.assertNotIn('PRIVATE-CONTENT', str(caught.exception))

    def test_versioned_example(self):
        config = load_config(ROOT/'agent/beispiele/konfiguration.yaml')
        self.assertEqual(config['adapters']['kubevirt']['timeoutSeconds'], 30)


if __name__ == '__main__':
    unittest.main()

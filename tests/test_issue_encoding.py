import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('issues_encoding', ROOT/'scripts/issues.py')
issues = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issues)


class EncodingTests(unittest.TestCase):
    def test_gh_reads_utf8_with_windows_default(self):
        run = subprocess.run

        def windows_run(command, **kwargs):
            kwargs.setdefault('encoding', 'cp1252')
            return run([sys.executable, '-c',
                        "import sys; sys.stdout.buffer.write('über Änderungen'.encode('utf-8'))"], **kwargs)

        with patch.object(issues.subprocess, 'run', side_effect=windows_run):
            self.assertEqual(issues.gh('api', 'test'), 'über Änderungen')

    def test_update_repairs_title_and_preserves_body(self):
        title = 'US04: Dokumentation über GitHub Pages'
        body = '## Prüfung\n\n- [ ] Änderungen prüfen'
        story = dict(id='US04', title=title, body=body, points=2,
                     sprint=1, epic='E1', priority='must')
        original = dict(number=4, title=title.encode('utf-8').decode('cp1252'),
                        body=issues.marked(body.replace('[ ]', '[x]')),
                        state='open', updated_at='2026-09-19T12:00:00Z', labels=[])
        edits = []
        read = Path.read_text
        write = Path.write_text

        def windows_read(path, encoding=None, errors=None):
            return read(path, encoding=encoding or 'cp1252', errors=errors)

        def windows_write(path, data, encoding=None, errors=None, **kwargs):
            return write(path, data, encoding=encoding or 'cp1252', errors=errors, **kwargs)

        def fake_gh(*args):
            if args[0] == 'api':
                return json.dumps([[original]] if '--paginate' in args else original, ensure_ascii=False)
            self.assertEqual(args[:2], ('issue', 'edit'))
            self.assertEqual(args[args.index('--title') + 1], title)
            text = Path(args[args.index('--body-file') + 1]).read_bytes().decode('utf-8')
            self.assertIn('- [x] Änderungen prüfen', text)
            self.assertNotIn('Ã', text)
            edits.append(args)
            return ''

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'scripts').mkdir()
            (root/'scripts/backlog.json').write_bytes(json.dumps([story], ensure_ascii=False).encode('utf-8'))
            with patch.object(issues, 'ROOT', root), patch.object(issues, 'gh', side_effect=fake_gh), \
                    patch.object(Path, 'read_text', windows_read), patch.object(Path, 'write_text', windows_write), \
                    patch.object(sys, 'argv', ['issues.py', 'update', 'test/repo', '--apply']), \
                    patch('sys.stdout', new=io.StringIO()):
                self.assertEqual(issues.main(), 0)
            self.assertEqual(len(edits), 1)


if __name__ == '__main__':
    unittest.main()

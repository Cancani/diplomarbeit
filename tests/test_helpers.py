import importlib.util
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/file)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
issues = load('issues', 'issues.py')
probe = load('probe', 'probe-http.py')


class IssueTests(unittest.TestCase):
    def setUp(self):
        self.story = dict(body='## Aufgabe\n\n- [ ] behalten\n- [ ] neu', previous_body='## Aufgabe\n\n- [ ] behalten\n- [ ] alt')

    def test_preserve_checked_and_retired(self):
        result = issues.migrate_body('## Aufgabe\n\n- [x] behalten\n- [x] alt', self.story)
        self.assertIn('- [x] behalten', result)
        self.assertIn('- [ ] neu', result)
        self.assertIn(issues.HISTORY+'\n\n- [x] alt', result)
        self.assertEqual(issues.migrate_body(result, self.story), result)

    def test_reject_user_changes(self):
        with self.assertRaises(ValueError):
            issues.migrate_body(self.story['previous_body']+'\nEigene wichtige Notiz', self.story)

    def test_notes_outside_block_survive(self):
        current = 'Meine Notiz\n'+issues.marked(self.story['body'])+'\nBeleg: Beispiel'
        self.assertEqual(issues.migrate_body(current, self.story), current)

    def test_missing_and_duplicate_issue(self):
        self.assertIsNone(issues.select_issue([], 'US01'))
        self.assertIsNone(issues.select_issue([{'title':'US010: anders'}], 'US01'))
        with self.assertRaises(ValueError):
            issues.select_issue([{'title':'US01: a'}, {'title':'US01: b'}], 'US01')

    def test_pagination_filters_pull_requests(self):
        with patch.object(issues, 'gh', return_value=json.dumps([[{'title':'US01: a'}], [{'title':'PR', 'pull_request':{}}, {'title':'US39: b'}]])):
            self.assertEqual(len(issues.list_issues('a/b')), 2)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/redirect':
            self.send_response(302); self.send_header('Location','/ok'); self.end_headers(); return
        self.send_response(200); self.end_headers()
        self.wfile.write(b'lernumgebung bereit\n' if self.path == '/ok' else b'falscher Inhalt')
    def log_message(self, *args): pass


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def test_content_and_timeout_and_no_redirect(self):
        for path, expected in [('/ok',0),('/wrong',1),('/redirect',1)]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                output = Path(temp)/'log.jsonl'
                result = probe.observe(self.base+path, 'local-test', output, timeout=.12, interval=.02, request_timeout=.04)
                self.assertEqual(result, expected)
                rows = [json.loads(x) for x in output.read_text().splitlines()]
                self.assertEqual(rows[-1]['event'], 'ready_observed' if expected == 0 else 'timeout')
                self.assertTrue(all(x['time_utc'].endswith('+00:00') for x in rows))
                with self.assertRaises(FileExistsError):
                    probe.observe(self.base+path, 'repeat', output)

    def test_invalid_timing(self):
        with self.assertRaises(ValueError):
            probe.observe(self.base, 'x', 'unused.jsonl', interval=0)

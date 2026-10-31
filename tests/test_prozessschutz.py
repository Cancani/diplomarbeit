from contextlib import closing, redirect_stdout
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.lebenszyklus import create, reset
from agent.zustand import StateError, StateStore
from adapter.vertrag import AdapterError
from gemeinsam.prozessschutz import adapter_guard, ProcessGuardError, run_guard
from modell.validierung import load_model
from test_kubevirt_lifecycle import http_endpoint


def wait_for(path, process):
    deadline = time.monotonic() + 10
    while not path.exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise AssertionError('Der Testprozess hat keine Bereitschaft gemeldet.')
        time.sleep(0.02)


class ProcessGuardTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.state = self.root/'state.sqlite3'

    def process(self, mode, ready, **env):
        process = subprocess.Popen(
            [sys.executable, str(ROOT/'tests/fixtures/process_guard.py'), mode, str(ready), str(self.state)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=dict(os.environ, **env))

        def stop():
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            process.stdin.close()

        self.addCleanup(stop)
        return process

    def test_adapter_blocks_takeover_after_agent_kill_and_stale_session_cannot_run(self):
        ready = self.root/'agent.json'
        agent = self.process('agent', ready)
        wait_for(ready, agent)
        session = json.loads(ready.read_text(encoding='utf-8'))
        adapter_ready = self.root/'adapter.json'
        adapter = self.process('adapter', adapter_ready, **session)
        wait_for(adapter_ready, adapter)
        agent.kill()
        agent.wait(timeout=10)
        with self.assertRaises(ProcessGuardError):
            with run_guard(self.state, 'test-run'):
                self.fail('Der noch aktive Adapter muss eine Übernahme verhindern.')
        # Ein anderer Lauf bleibt unabhängig ausführbar.
        with run_guard(self.state, 'other-run'):
            pass
        adapter.stdin.close()
        self.assertEqual(adapter.wait(timeout=10), 0)
        with run_guard(self.state, 'test-run') as new_session:
            self.assertNotEqual(session, new_session)
            with patch.dict(os.environ, session), self.assertRaises(ProcessGuardError):
                with adapter_guard():
                    self.fail('Die alte Sitzung darf keine Werkzeugausführung mehr beginnen.')
            with patch.dict(os.environ, new_session), adapter_guard():
                pass

    def test_schema_four_migration_does_not_treat_legacy_running_operation_as_dead(self):
        model = load_model(ROOT/'modell/beispiele/referenz.yaml')
        store = StateStore(self.state)
        store.start_create('test-run', 'create-01', 'kubevirt', model)
        store.record_resource('test-run', 'create-01', 'VirtualMachine', 'known-uid')
        with closing(sqlite3.connect(self.state)) as connection:
            connection.execute('ALTER TABLE operations DROP COLUMN guarded')
            connection.execute('PRAGMA user_version = 4')
        config = {'stateFile': self.state, 'adapters': {'kubevirt': {}}}
        with patch('agent.lebenszyklus.call_tool') as call, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(StateError, 'Altauftrag'):
                reset(config, 'test-run', 'reset-01')
        call.assert_not_called()
        record = StateStore(self.state).get('test-run')
        self.assertEqual(record['operation']['guarded'], 0)
        self.assertEqual(record['operation']['status'], 'running')
        self.assertEqual(record['resources'][0]['resource_id'], 'known-uid')

    def test_killed_agent_recovers_lost_create_response_over_real_mcp_without_duplicate(self):
        actual = self.root/'platform.json'
        with http_endpoint() as url:
            settings = {'command': sys.executable, 'args': [str(ROOT/'tests/fixtures/crash_adapter.py'),
                        str(actual), str(self.state), url], 'timeoutSeconds': 10}
            config_path = self.root/'config.yaml'
            config_path.write_text(yaml.safe_dump({'stateFile': str(self.state),
                                  'adapters': {'kubevirt': settings}}), encoding='utf-8')
            with (self.root/'agent.log').open('w') as log:
                agent = subprocess.Popen([sys.executable, '-m', 'agent', '--config', str(config_path),
                        'create', str(ROOT/'modell/beispiele/referenz.yaml'), '--platform', 'kubevirt',
                        '--run-id', 'test-run', '--operation-id', 'create-01'],
                        cwd=ROOT, stdout=log, stderr=log)
                try:
                    wait_for(actual.with_suffix('.ready'), agent)
                    record = StateStore(self.state).get('test-run')
                    self.assertEqual(record['operation']['status'], 'running')
                    self.assertEqual(record['operation']['guarded'], 1)
                    self.assertEqual(record['resources'], [])
                    agent.kill()
                    agent.wait(timeout=10)
                finally:
                    if agent.poll() is None:
                        agent.kill()
                        agent.wait(timeout=10)
                    actual.with_suffix('.release').touch()
            # Das Ende des Agenten allein gibt eine noch aktive Adapterarbeit
            # nicht frei. Erst nach deren Ende wird die Sperre erhältlich.
            deadline = time.monotonic() + 15
            while True:
                try:
                    with run_guard(self.state, 'test-run'):
                        break
                except ProcessGuardError:
                    if time.monotonic() > deadline:
                        self.fail('Der alte Adapter hat seine Sperre nicht freigegeben.')
                    time.sleep(0.02)
            config = {'stateFile': self.state, 'adapters': {'kubevirt': settings}}
            output = io.StringIO()
            with redirect_stdout(output):
                create(config, 'test-run', 'create-01', 'kubevirt',
                       load_model(ROOT/'modell/beispiele/referenz.yaml'))
            events = [json.loads(line)['event'] for line in output.getvalue().splitlines()]
            self.assertEqual(events[0], 'operation_recovered')
            self.assertEqual(events[-1], 'ready')
            record = StateStore(self.state).get('test-run')
            self.assertEqual(record['phase'], 'ready')
            self.assertEqual(record['operation']['status'], 'succeeded')
            self.assertEqual([r['resource_id'] for r in record['resources']], ['unchanged-uid'])

    def test_failed_reconciliation_preserves_running_operation_and_known_resources(self):
        model = load_model(ROOT/'modell/beispiele/referenz.yaml')
        store = StateStore(self.state)
        store.start_create('test-run', 'create-01', 'kubevirt', model, guarded=True)
        store.record_resource('test-run', 'create-01', 'VirtualMachine', 'known-uid')
        before = store.get('test-run')
        config = {'stateFile': self.state, 'adapters': {'kubevirt': {}}}
        with patch('agent.lebenszyklus.call_tool', side_effect=AdapterError('timeout')) as call, \
                redirect_stdout(io.StringIO()), self.assertRaises(AdapterError):
            create(config, 'test-run', 'create-01', 'kubevirt', model)
        self.assertEqual([args.args[1] for args in call.call_args_list], ['status'])
        self.assertEqual(store.get('test-run'), before)


if __name__ == '__main__':
    unittest.main()

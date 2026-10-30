from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.zustand import StateError, StateStore
from modell.validierung import load_model, ModelValidationError


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)/'state'/'zustand.sqlite3'
        self.store = StateStore(self.path)
        self.model = load_model(ROOT/'modell/beispiele/referenz.yaml')

    def create(self, run='lokal-01', operation='create-01'):
        self.store.start_create(run, operation, 'kubevirt', self.model)

    def ready(self):
        self.create()
        self.store.record_resource('lokal-01', 'create-01', 'VirtualMachine', 'vm-uid', 'default')
        self.store.advance('lokal-01', 'create-01', 'ready')

    def test_snapshot_survives_reopening_and_cannot_be_replaced(self):
        self.create()
        record = StateStore(self.path).get('lokal-01')
        snapshot = json.dumps(self.model, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.assertEqual(record['model_snapshot'], self.model)
        self.assertEqual(record['model_hash'], hashlib.sha256(snapshot.encode('utf-8')).hexdigest())
        self.assertEqual(record['platform'], 'kubevirt')
        self.assertEqual(record['phase'], 'creating')
        self.assertEqual(record['operation']['operation_id'], 'create-01')
        changed = deepcopy(self.model)
        changed['vm']['resources']['minMemoryMiB'] += 1024
        for model, platform in [(changed, 'kubevirt'), (self.model, 'aws')]:
            with self.subTest(platform=platform), self.assertRaises(StateError):
                self.store.start_create('lokal-01', 'replacement', platform, model)
        record['model_snapshot']['vm']['resources']['minMemoryMiB'] = 0
        self.assertEqual(self.store.get('lokal-01')['model_snapshot'], self.model)

    def test_concurrent_start_has_one_winner_and_does_not_block_other_runs(self):
        barrier = Barrier(2)

        def start(operation):
            barrier.wait(timeout=5)
            try:
                self.create(operation=operation)
                return 'started'
            except StateError:
                return 'blocked'

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(start, ['writer-1', 'writer-2']))
        self.assertCountEqual(results, ['started', 'blocked'])
        active = self.store.get('lokal-01')['operation']['operation_id']
        with self.assertRaises(StateError):
            self.create(operation=active)  # Gleiche Kennung ist keine zweite Schreibberechtigung.
        self.create('lokal-02', 'other-run')
        self.assertEqual(self.store.get('lokal-02')['phase'], 'creating')
        with self.assertRaises(StateError):
            self.create('lokal-03', active)
        with self.assertRaises(StateError):
            self.store.get('lokal-03')  # Auch der neue Lauf wurde zurückgerollt.

    def test_reset_requires_confirmed_removal_before_recreation(self):
        self.ready()
        for phase in ['absent', 'deleting']:
            with self.subTest(phase=phase), self.assertRaises(StateError):
                self.store.advance('lokal-01', 'create-01', phase)
        self.store.start_operation('lokal-01', 'reset-01', 'reset')
        with self.assertRaises(StateError):
            self.store.advance('lokal-01', 'reset-01', 'ready')
        with self.assertRaises(StateError):
            self.store.advance('lokal-01', 'reset-01', 'creating')
        self.store.confirm_removed('lokal-01', 'reset-01', 'VirtualMachine', 'vm-uid', 'default')
        self.store.advance('lokal-01', 'reset-01', 'creating')
        with self.assertRaises(StateError):
            self.store.advance('lokal-01', 'reset-01', 'ready')
        self.store.record_resource('lokal-01', 'reset-01', 'VirtualMachine', 'new-uid', 'default')
        self.store.advance('lokal-01', 'reset-01', 'ready')
        record = self.store.get('lokal-01')
        self.assertEqual(record['phase'], 'ready')
        self.assertEqual(record['operation']['status'], 'succeeded')
        self.assertEqual(record['model_snapshot'], self.model)
        self.assertEqual([r['resource_id'] for r in record['resources']], ['new-uid'])
        with self.assertRaises(StateError):
            self.store.confirm_removed('lokal-01', 'reset-01', 'VirtualMachine', 'new-uid', 'default')

    def test_timeout_and_failed_cleanup_keep_inventory_until_confirmed_absent(self):
        self.create()
        for _ in range(2):
            self.store.record_resource('lokal-01', 'create-01', 'PersistentVolume', 'pv-uid')
        self.store.fail('lokal-01', 'create-01', 'timeout')
        record = StateStore(self.path).get('lokal-01')
        self.assertEqual(record['phase'], 'error')
        self.assertEqual(record['operation']['error_code'], 'timeout')
        self.assertEqual(len(record['resources']), 1)
        self.store.start_operation('lokal-01', 'delete-01', 'delete')
        with self.assertRaises(StateError):
            self.store.advance('lokal-01', 'delete-01', 'absent')
        self.store.fail('lokal-01', 'delete-01', 'platform_error')
        self.assertEqual(len(self.store.get('lokal-01')['resources']), 1)
        self.store.start_operation('lokal-01', 'delete-02', 'delete')
        self.store.confirm_removed('lokal-01', 'delete-02', 'PersistentVolume', 'pv-uid')
        self.store.advance('lokal-01', 'delete-02', 'absent')
        self.store.start_operation('lokal-01', 'delete-03', 'delete')
        record = self.store.get('lokal-01')
        self.assertEqual((record['phase'], record['resources']), ('absent', []))
        self.assertEqual(record['operation']['status'], 'succeeded')
        # Eine neue Erstellung desselben Laufs verwendet denselben Snapshot und Hash.
        reordered = dict(reversed(list(self.model.items())))
        self.store.start_create('lokal-01', 'create-02', 'kubevirt', reordered)
        self.assertEqual(self.store.get('lokal-01')['model_hash'], record['model_hash'])

    def test_process_abort_keeps_operation_and_blocks_unreconciled_restart(self):
        script = '''
import os
from agent.zustand import StateStore
from modell.validierung import load_model
store = StateStore(__import__('sys').argv[1])
store.start_create('crash-run', 'crash-operation', 'kubevirt', load_model(__import__('sys').argv[2]))
store.record_resource('crash-run', 'crash-operation', 'VirtualMachine', 'known-uid', 'default')
os._exit(23)
'''
        result = subprocess.run(
            [sys.executable, '-c', script, str(self.path), str(ROOT/'modell/beispiele/referenz.yaml')],
            cwd=self.path.parent, env=dict(os.environ, PYTHONPATH=str(ROOT)),
            capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 23, result.stderr)
        record = StateStore(self.path).get('crash-run')
        self.assertEqual(record['operation']['status'], 'running')
        self.assertEqual(record['resources'][0]['resource_id'], 'known-uid')
        with self.assertRaises(StateError):
            self.store.start_operation('crash-run', 'unsafe-delete', 'delete')
        with self.assertRaises(StateError):
            self.store.start_create('crash-run', 'unsafe-create', 'kubevirt', self.model)

    def test_invalid_inputs_and_unknown_database_version_are_rejected(self):
        invalid = deepcopy(self.model)
        invalid['vm']['resources']['minMemoryMiB'] = 0
        with self.assertRaises(ModelValidationError):
            self.store.start_create('invalid', 'invalid-operation', 'kubevirt', invalid)
        with self.assertRaises(StateError):
            self.store.get('invalid')
        self.create()
        with self.assertRaises(StateError):
            self.store.fail('lokal-01', 'create-01', 'PRIVATE-CONTENT')
        self.assertEqual(self.store.get('lokal-01')['phase'], 'creating')
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute('PRAGMA user_version = 99')
        with self.assertRaises(StateError):
            StateStore(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 99)

    def test_schema_migration_keeps_existing_operation_and_resource_id(self):
        store = StateStore(self.path)
        store.start_create('run-01', 'operation-01', 'kubevirt', self.model)
        store.record_resource('run-01', 'operation-01', 'VirtualMachine', 'vm-id', 'diplomarbeit-agent')
        with closing(sqlite3.connect(self.path, isolation_level=None)) as connection:
            connection.execute('ALTER TABLE resources DROP COLUMN name')
            connection.execute('PRAGMA user_version = 1')
        record = StateStore(self.path).get('run-01')
        self.assertEqual(record['operation']['operation_id'], 'operation-01')
        self.assertEqual(record['resources'][0]['resource_id'], 'vm-id')
        self.assertEqual(record['resources'][0]['name'], '')

    def test_database_limit_includes_pending_and_failed_runs_and_serializes_admission(self):
        store = StateStore(self.path)
        for index in range(29):
            store.start_create(f'run-{index}', f'op-{index}',
                               'aws' if index % 2 else 'kubevirt', self.model)
            if index % 3 == 0:
                store.fail(f'run-{index}', f'op-{index}', 'timeout')
        barrier = Barrier(2)

        def start(index):
            barrier.wait(timeout=5)
            try:
                store.start_create(f'run-{index}', f'op-{index}', 'kubevirt', self.model)
                return 'started'
            except StateError:
                return 'blocked'

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(start, [29, 30])), ['started', 'blocked'])
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM runs').fetchone()[0], 30)


if __name__ == '__main__':
    unittest.main()

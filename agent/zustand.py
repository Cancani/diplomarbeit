"""SQLite-Zustand und Übergänge; Plattformabfragen erfolgen im Lebenszyklus."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from modell.snapshot import encode_snapshot


SCHEMA = (
    """CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        platform TEXT NOT NULL CHECK (platform IN ('kubevirt', 'aws')),
        model_snapshot TEXT NOT NULL,
        model_hash TEXT NOT NULL,
        phase TEXT NOT NULL CHECK (phase IN ('absent', 'creating', 'ready', 'deleting', 'error')),
        operation_id TEXT,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS operations (
        operation_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        kind TEXT NOT NULL CHECK (kind IN ('create', 'reset', 'delete')),
        status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
        error_code TEXT,
        started_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS one_running_operation
        ON operations(run_id) WHERE status = 'running'""",
    """CREATE TABLE IF NOT EXISTS resources (
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        kind TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        PRIMARY KEY (run_id, kind, resource_id, scope)
    )""",
)

TRANSITIONS = {
    ('create', 'creating', 'ready'),
    ('reset', 'deleting', 'creating'),
    ('reset', 'creating', 'ready'),
    ('delete', 'deleting', 'absent'),
}


class StateError(ValueError):
    """Ungültiger Auftrag oder nicht verfügbarer Zustandsspeicher."""


def require_text(*values):
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise StateError('Kennungen und Ressourcentypen müssen nicht leere Texte sein.')


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class StateStore:
    def __init__(self, path):
        self.path = Path(path)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise StateError('Zustandsordner konnte nicht angelegt werden.') from error
        with self.connection(write=True) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1, 2):
                raise StateError('Die Version des Zustandsspeichers wird nicht unterstützt.')
            for statement in SCHEMA:
                connection.execute(statement)
            if version == 1:
                connection.execute("ALTER TABLE resources ADD COLUMN name TEXT NOT NULL DEFAULT ''")
            connection.execute('PRAGMA user_version = 2')

    @contextmanager
    def connection(self, write=False):
        connection = None
        try:
            connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA foreign_keys = ON')
            connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield connection
            connection.commit()
        except sqlite3.Error as error:
            raise StateError('Zustandsspeicher ist nicht verfügbar oder der Auftrag widerspricht dem gespeicherten Zustand.') from error
        finally:
            if connection is not None:
                connection.close()  # Eine offene Transaktion wird zurückgerollt.

    def _run(self, connection, run_id):
        row = connection.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
        if row is None:
            raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
        return row

    def _active(self, connection, run_id, operation_id):
        row = connection.execute(
            "SELECT * FROM operations WHERE run_id = ? AND operation_id = ? AND status = 'running'",
            (run_id, operation_id)).fetchone()
        if row is None:
            raise StateError('Die Operation ist für diesen Lauf nicht aktiv.')
        return row

    def _start(self, connection, run_id, operation_id, kind):
        require_text(run_id, operation_id)
        run = self._run(connection, run_id)
        if connection.execute("SELECT 1 FROM operations WHERE run_id = ? AND status = 'running'",
                              (run_id,)).fetchone():
            raise StateError('Für diesen Lauf ist bereits eine schreibende Operation aktiv; zuerst ist ein Plattformabgleich nötig.')
        allowed = {'create': {'absent'}, 'reset': {'ready'}, 'delete': {'ready', 'error', 'absent'}}
        if run['phase'] not in allowed[kind]:
            raise StateError('Die Operation ist in der gespeicherten Phase nicht zulässig.')
        if kind == 'create' and connection.execute(
                "SELECT COUNT(*) FROM runs WHERE phase <> 'absent'").fetchone()[0] >= 30:
            raise StateError('Die Obergrenze von 30 reservierten oder vorhandenen VMs ist erreicht.')
        if connection.execute('SELECT 1 FROM operations WHERE operation_id = ?',
                              (operation_id,)).fetchone():
            raise StateError('Die Operationskennung wurde bereits verwendet.')
        phase = 'creating' if kind == 'create' else 'deleting'
        status = 'running'
        if kind == 'delete' and run['phase'] == 'absent':
            phase, status = 'absent', 'succeeded'
        now = timestamp()
        connection.execute('INSERT INTO operations VALUES (?, ?, ?, ?, NULL, ?, ?)',
                           (operation_id, run_id, kind, status, now, now))
        connection.execute('UPDATE runs SET phase = ?, operation_id = ?, updated_at = ? WHERE run_id = ?',
                           (phase, operation_id, now, run_id))

    def start_create(self, run_id, operation_id, platform, model):
        """Modell und Auftrag vor dem ersten Plattformaufruf atomar speichern."""
        require_text(run_id, operation_id)
        if platform not in ('kubevirt', 'aws'):
            raise StateError('Die Zielplattform wird nicht unterstützt.')
        snapshot, digest = encode_snapshot(model)
        with self.connection(write=True) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO runs VALUES (?, ?, ?, ?, 'absent', NULL, ?)",
                (run_id, platform, snapshot, digest, timestamp()))
            run = self._run(connection, run_id)
            if run['platform'] != platform or run['model_snapshot'] != snapshot:
                raise StateError('Plattform und Modell-Snapshot eines Laufs dürfen nicht verändert werden.')
            self._start(connection, run_id, operation_id, 'create')

    def start_operation(self, run_id, operation_id, kind):
        """Reset oder Abbau für eine bereits gespeicherte Umgebung beginnen."""
        if kind not in ('reset', 'delete'):
            raise StateError('Hier sind nur reset und delete zulässig.')
        with self.connection(write=True) as connection:
            self._start(connection, run_id, operation_id, kind)

    def record_resource(self, run_id, operation_id, kind, resource_id, scope='', name=''):
        """Eine erstellte oder beim Abgleich gefundene Ressource speichern."""
        require_text(kind, resource_id)
        if not isinstance(scope, str):
            raise StateError('Der Ressourcenbereich muss ein Text sein.')
        with self.connection(write=True) as connection:
            self._active(connection, run_id, operation_id)
            self._record(connection, run_id, kind, resource_id, scope, name)

    def _record(self, connection, run_id, kind, resource_id, scope, name):
        connection.execute(
            'INSERT INTO resources (run_id, kind, resource_id, scope, name) VALUES (?, ?, ?, ?, ?) '
            "ON CONFLICT (run_id, kind, resource_id, scope) DO UPDATE SET name = CASE "
            "WHEN excluded.name <> '' THEN excluded.name ELSE resources.name END",
            (run_id, kind, resource_id, scope, name))

    def observe_resources(self, run_id, operation_id, resources):
        """Inventar ergänzen; ein zwischenzeitlich neuer Auftrag weist alte Antworten ab."""
        with self.connection(write=True) as connection:
            run = self._run(connection, run_id)
            if run['operation_id'] != operation_id or (run['phase'] == 'absent' and resources):
                raise StateError('Der Laufzustand hat sich geändert; Status erneut abfragen.')
            for resource in resources:
                self._record(connection, run_id, resource['kind'], resource['resource_id'],
                             resource['scope'], resource['name'])

    def confirm_removed(self, run_id, operation_id, kind, resource_id, scope=''):
        """Erst nach bestätigter Abwesenheit auf der Plattform aufrufen."""
        with self.connection(write=True) as connection:
            self._active(connection, run_id, operation_id)
            if self._run(connection, run_id)['phase'] != 'deleting':
                raise StateError('Ressourcen dürfen nur während des Abbaus ausgetragen werden.')
            connection.execute('DELETE FROM resources WHERE run_id = ? AND kind = ? AND resource_id = ? AND scope = ?',
                               (run_id, kind, resource_id, scope))

    def advance(self, run_id, operation_id, phase):
        """Nach Readiness-Prüfung oder vollständiger Abbaukontrolle fortschalten."""
        with self.connection(write=True) as connection:
            operation = self._active(connection, run_id, operation_id)
            run = self._run(connection, run_id)
            if (operation['kind'], run['phase'], phase) not in TRANSITIONS:
                raise StateError('Dieser Zustandsübergang ist nicht zulässig.')
            has_resources = connection.execute('SELECT 1 FROM resources WHERE run_id = ?',
                                               (run_id,)).fetchone() is not None
            if run['phase'] == 'deleting' and has_resources:
                raise StateError('Der Abbau ist noch nicht vollständig bestätigt.')
            if phase == 'ready' and not has_resources:
                raise StateError('Ohne gespeicherte Ressourcen kann die Umgebung nicht bereit sein.')
            now = timestamp()
            connection.execute('UPDATE runs SET phase = ?, updated_at = ? WHERE run_id = ?',
                               (phase, now, run_id))
            if phase in ('ready', 'absent'):
                connection.execute("UPDATE operations SET status = 'succeeded', updated_at = ? WHERE operation_id = ?",
                                   (now, operation_id))

    def fail(self, run_id, operation_id, error_code):
        """Fehler speichern und das bekannte Ressourceninventar erhalten."""
        if error_code not in ('timeout', 'platform_error', 'interrupted'):
            raise StateError('Unbekannter Fehlercode; freie Fehlermeldungen werden nicht gespeichert.')
        with self.connection(write=True) as connection:
            self._active(connection, run_id, operation_id)
            now = timestamp()
            connection.execute("UPDATE operations SET status = 'failed', error_code = ?, updated_at = ? WHERE operation_id = ?",
                               (error_code, now, operation_id))
            connection.execute("UPDATE runs SET phase = 'error', updated_at = ? WHERE run_id = ?",
                               (now, run_id))

    def get(self, run_id):
        """Gespeicherten Stand lesen; dies ist keine Plattform-Statusabfrage."""
        with self.connection() as connection:
            run = dict(self._run(connection, run_id))
            run['model_snapshot'] = json.loads(run['model_snapshot'])
            run['operation'] = dict(connection.execute(
                'SELECT * FROM operations WHERE operation_id = ?', (run.pop('operation_id'),)).fetchone())
            run['resources'] = [dict(row) for row in connection.execute(
                'SELECT kind, resource_id, scope, name FROM resources WHERE run_id = ? ORDER BY kind, resource_id, scope',
                (run_id,))]
            return run

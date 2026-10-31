"""Lokale Prozesssperre mit SQLite-Lesetransaktionen und Sitzungskennung.

Eine neue Sitzung braucht exklusiven Zugriff. Agent und Adapter halten danach
Lesetransaktionen, bis ihre Arbeit beendet ist. Sperrdateien nicht löschen:
Ein anderer Dateiname würde die noch vorhandenen Sperren umgehen.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sqlite3
import uuid


GUARD_PATH = 'DIPLOMARBEIT_RUN_GUARD'
GUARD_TOKEN = 'DIPLOMARBEIT_RUN_TOKEN'


class ProcessGuardError(ValueError):
    pass


def _read_session(connection, expected):
    connection.execute('BEGIN')
    rows = connection.execute('SELECT token FROM session').fetchall()
    if rows != [(expected,)]:
        raise ProcessGuardError('Die Prozesssitzung wurde abgelöst; Auftrag erneut prüfen.')


@contextmanager
def run_guard(state_file, run_id):
    """Nur ohne aktive Leser eine neue Sitzung beginnen, dann lesend halten."""
    state_file = Path(state_file).resolve()
    path = state_file.parent/(state_file.name + '.agent-locks')/(hashlib.sha256(run_id.encode()).hexdigest() + '.sqlite3')
    connection = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=0, isolation_level=None)
        connection.execute('BEGIN EXCLUSIVE')
        connection.execute('CREATE TABLE IF NOT EXISTS session (token TEXT NOT NULL)')
        token = uuid.uuid4().hex
        connection.execute('DELETE FROM session')
        connection.execute('INSERT INTO session VALUES (?)', (token,))
        connection.commit()
        # Beim Wechsel zur Lesetransaktion kann ein anderer Starter gewinnen.
        # Deshalb muss die Kennung unter der erworbenen Lesesperre noch passen.
        _read_session(connection, token)
        yield {GUARD_PATH: str(path), GUARD_TOKEN: token}
    except (OSError, sqlite3.Error) as error:
        raise ProcessGuardError('Für diesen Lauf ist noch ein Agent oder Adapter aktiv oder die Prozesssperre ist nicht verfügbar.') from error
    finally:
        if connection is not None:
            connection.close()


@contextmanager
def adapter_guard():
    """Adapter und seine Werkzeugausführung an die aktuelle Sitzung binden."""
    path, token = os.environ.get(GUARD_PATH), os.environ.get(GUARD_TOKEN)
    if path is None and token is None:
        yield
        return
    if not path or not token:
        raise ProcessGuardError('Die Prozesssitzung des Adapters ist unvollständig.')
    connection = None
    try:
        # Ohne vorhandene Sperrdatei darf kein verspäteter Adapter sie neu anlegen.
        connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro',
                                     uri=True, timeout=0, isolation_level=None)
        _read_session(connection, token)
        yield
    except (OSError, sqlite3.Error) as error:
        raise ProcessGuardError('Die Prozesssitzung des Adapters ist nicht verfügbar.') from error
    finally:
        if connection is not None:
            connection.close()

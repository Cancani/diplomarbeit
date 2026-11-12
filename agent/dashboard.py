"""Lokale Nur-Lese-Übersicht für den PoC."""
import argparse
from contextlib import closing
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
from urllib.parse import parse_qs, urlencode, urlsplit

from adapter.vertrag import AdapterError
from agent.konfiguration import ConfigurationError, load_config
from agent.lebenszyklus import inspect_status
from agent.zustand import StateError


PLATFORMS = {'kubevirt': 'KubeVirt', 'aws': 'AWS EC2'}
PHASES = {'creating': 'Wird erstellt', 'ready': 'Bereit',
          'deleting': 'Wird abgebaut', 'error': 'Fehler', 'absent': 'Abgebaut'}
STYLE = """
* { box-sizing: border-box; }
body { margin: 0; background: #f6f5f3; color: #24262a;
       font: 1rem/1.55 'Inter', system-ui, sans-serif; }
main { width: min(68rem, 100% - 2rem); margin: 4rem auto; }
h1 { font-size: clamp(2rem, 5vw, 3.2rem); line-height: 1.1; margin: 0; }
p { color: #555b65; }
.table { overflow-x: auto; background: #fff; border: 1px solid #dedbd7;
         border-top: 3px solid #97162a; }
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: .85rem 1rem; border-bottom: 1px solid #e8e5e2; }
th { background: #fcfbfa; font-size: .875rem; white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
a { color: #831529; text-underline-offset: .18em; white-space: nowrap; }
code { overflow-wrap: anywhere; }
"""


def read_runs(path):
    """Laufübersicht aus SQLite lesen, ohne die Datenbank zu initialisieren."""
    if not path.is_file():
        return []
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT run_id, platform, phase, model_hash, model_snapshot FROM runs "
            "ORDER BY phase = 'absent', updated_at DESC, run_id")]


def page(config, selected):
    try:
        runs = read_runs(config['stateFile'])
    except sqlite3.Error:
        return '<p>Der Zustandsspeicher ist momentan nicht lesbar.</p>'
    if not runs:
        return '<p>In dieser Agent-Konfiguration sind noch keine Läufe gespeichert.</p>'

    rows = []
    for run in runs:
        run_id = run['run_id']
        vm, http = '—', '—'
        if run_id == selected:
            try:
                run['model_snapshot'] = json.loads(run['model_snapshot'])
                actual, ready = inspect_status(config, run)
                vm = actual['vmState']
                http = 'Bereit' if ready else 'Nicht bereit'
            except (AdapterError, StateError, ValueError):
                vm = 'Abfrage fehlgeschlagen'
        phase = PHASES.get(run['phase'], run['phase'])
        platform = PLATFORMS.get(run['platform'], run['platform'])
        link = escape('?' + urlencode({'run': run_id}), quote=True)
        rows.append(f'<tr><td><code>{escape(run_id)}</code></td><td>{escape(platform)}</td>'
                    f'<td>{escape(phase)}</td><td>{escape(vm)}</td><td>{escape(http)}</td>'
                    f'<td><a href="{link}" aria-label="Status für {escape(run_id)} prüfen">'
                    'Status prüfen</a></td></tr>')

    return ('<div class="table"><table><thead><tr><th scope="col">Laufkennung</th>'
            '<th scope="col">Plattform</th><th scope="col">Gespeicherte Phase</th>'
            '<th scope="col">VM-Status</th><th scope="col">HTTP-Bereitschaft</th>'
            '<th scope="col">Live-Abfrage</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></div>')


def make_handler(config):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path != '/':
                self.send_error(404)
                return
            selected = parse_qs(url.query).get('run', [None])[0]
            body = ('<!doctype html><html lang="de-CH"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">'
                    f'<title>Lernumgebungen</title><style>{STYLE}</style></head>'
                    '<body><main><h1>Lernumgebungen</h1>'
                    '<p>Gespeicherte Läufe. «Status prüfen» fragt die Plattform und den Testdienst ab.</p>'
                    f'{page(config, selected)}</main></body></html>').encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return DashboardHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, help='Pfad zur Agent-Konfiguration')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        with HTTPServer(('127.0.0.1', args.port), make_handler(config)) as server:
            print(f'Übersicht: http://127.0.0.1:{server.server_port}/', flush=True)
            server.serve_forever()
    except (ConfigurationError, OSError, OverflowError) as error:
        parser.exit(1, f'{error}\n')
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

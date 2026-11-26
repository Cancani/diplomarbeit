"""Lernumgebungen mit persistentem Zustand und Plattformadaptern steuern."""
import argparse
import os
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
import sqlite3
import sys
from threading import Event
import uuid

from modell.validierung import load_model, ModelValidationError
from agent.konfiguration import ConfigurationError, default_config_path, load_config
from agent.ausgabe import output_mode, platform_result, run_overview
from gemeinsam import MAX_VMS


JSON_HELP = 'Vollständige JSON-Ausgabe für Skripte und Protokolle'
RUN_ID_HELP = ('Name der Maschine, frei gewählt; bleibt für alle Befehle gleich '
               '(frühere Schreibweise: --run-id)')
OPERATION_ID_HELP = ('Operationskennung des Auftrags; wird ohne Angabe erzeugt und nur '
                     'angegeben, um einen unterbrochenen Auftrag fortzusetzen')
ID_RULE = ('Erlaubt sind Kleinbuchstaben, Ziffern und einzelne Bindestriche, '
           'höchstens 63 Zeichen. Beispiel: demo-01')
EXAMPLES = '''Begriffe:
  Name (--name)
      Frei gewählter Name der Maschine. Er bleibt für create, status, reset und
      delete gleich. Die frühere Schreibweise --run-id gilt weiter.
  Operationskennung (--operation-id)
      Kennung eines einzelnen Auftrags. Der Agent erzeugt sie selbst. Sie wird nur
      angegeben, um einen unterbrochenen Auftrag fortzusetzen.
  Anzahl (--count)
      Mehrere gleiche Lernumgebungen. Die Namen erhalten die Endungen -1, -2 usw.

Beispiele:
  python -m agent create modell/beispiele/referenz.yaml --platform kubevirt --name demo-01
  python -m agent status
  python -m agent status --name demo-01
  python -m agent reset --name demo-01
  python -m agent delete --name demo-01

Die Plattform wird nur bei create gewählt. Die übrigen Befehle lesen sie aus der
gespeicherten Lernumgebung.
'''


def positive_seconds(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('Die Zeitgrenze muss positiv sein.')
    return number


def vm_count(value):
    number = int(value)
    if not 1 <= number <= MAX_VMS:
        raise argparse.ArgumentTypeError(f'Die Anzahl muss zwischen 1 und {MAX_VMS} liegen.')
    return number


def build_parser():
    parser = argparse.ArgumentParser(
        prog='python -m agent', epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Lernumgebungen erstellen, prüfen, zurücksetzen und löschen.')
    parser.add_argument('--config', type=Path,
                        help='Agent-Konfiguration; hat Vorrang vor der Auswahl über --platform')
    parser.add_argument('--json', action='store_true', help=JSON_HELP)
    parser.set_defaults(count=1)
    commands = parser.add_subparsers(dest='operation', required=True)
    probe = commands.add_parser('platform-status', help='Plattform über MCP lesend prüfen')
    probe.add_argument('--json', action='store_true', default=argparse.SUPPRESS,
                       help=JSON_HELP)
    probe.add_argument('--platform', required=True, choices=('kubevirt', 'aws'),
                       help='Zu prüfende Plattform')
    descriptions = {
        'create': 'Lernumgebung aus einer YAML-Definition erstellen',
        'status': 'Übersicht der gespeicherten Lernumgebungen oder Zustand einer Lernumgebung abfragen',
        'reset': 'Lernumgebung aus dem gespeicherten Modell neu erstellen',
        'delete': 'Lernumgebung vollständig entfernen',
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument('--json', action='store_true', default=argparse.SUPPRESS,
                             help=JSON_HELP)
        if name == 'status':
            command.add_argument('--name', '--run-id', dest='run_id', metavar='NAME',
                                 help='Name der Maschine; ohne Angabe erscheint die '
                                      'Übersicht der vorhandenen Lernumgebungen')
            command.add_argument('--all', action='store_true',
                                 help='In der Übersicht auch abgebaute Lernumgebungen zeigen')
        else:
            command.add_argument('--name', '--run-id', dest='run_id', metavar='NAME',
                                 required=True, help=RUN_ID_HELP)
        if name != 'create':
            command.add_argument('--platform', choices=('kubevirt', 'aws'),
                                 help='Optional; ohne Angabe gilt die gespeicherte Plattform. '
                                      'Mit Angabe wird sie geprüft'
                                      + (', in der Übersicht gefiltert.' if name == 'status' else '.'))
        if name in ('create', 'status', 'delete'):
            command.add_argument('--count', type=vm_count, default=1,
                                 help='Anzahl gleicher Lernumgebungen; ab 2 erhalten die '
                                      'Namen die Endungen -1, -2 usw. (Standard: 1)')
        if name == 'create':
            command.add_argument('definition', type=Path, help='YAML-Datei der Lernumgebung')
            command.add_argument('--platform', required=True, choices=('kubevirt', 'aws'),
                                 help='Zielplattform')
            command.add_argument('--operation-id', help=OPERATION_ID_HELP)
            command.add_argument('--parallel', type=vm_count, default=1,
                                 help='Gleichzeitige KubeVirt-Erstellungsaufträge (Standard: 1).')
            command.add_argument('--timeout-seconds', type=positive_seconds, default=900,
                                 help='Gesamte Zeitgrenze bis zur HTTP-Bereitschaft (Standard: 900)')
        if name in ('reset', 'delete'):
            command.add_argument('--operation-id', help=OPERATION_ID_HELP)
            default_timeout = 1200 if name == 'reset' else 300
            command.add_argument('--timeout-seconds', type=positive_seconds, default=default_timeout,
                                 help=f'Gesamte Zeitgrenze der Operation (Standard: {default_timeout})')
    return parser


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.operation == 'status' and args.run_id is None and args.count != 1:
        parser.error('--count benötigt einen Namen mit --name.')
    if args.operation == 'status' and args.run_id is not None and args.all:
        parser.error('--all gilt nur für die Übersicht ohne --name.')
    try:
        with output_mode(args.json):
            return run(args)
    except BrokenPipeError:
        # Der Empfänger hat die Ausgabe geschlossen, zum Beispiel head. Ohne Traceback enden.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        print('Ausgabe wurde geschlossen; gespeicherten Zustand mit status prüfen.', file=sys.stderr)
        return 1


def run(args):
    source = args.config
    try:
        if source is None:
            # Ohne Plattformangabe liegt der Zustand bei der lokalen Standardkonfiguration.
            source = default_config_path(getattr(args, 'platform', None) or 'kubevirt')
        config = load_config(source)
    except ConfigurationError as error:
        hint = (f' Standardkonfiguration: {source}. '
                'Eine andere Datei kann mit --config gewählt werden.'
                if args.config is None and source is not None else '')
        print(f'Konfigurationsfehler: {error}{hint}', file=sys.stderr)
        return 1
    if args.operation in ('platform-status', 'create') and args.platform not in config['adapters']:
        print(f'Für die Zielplattform {args.platform} ist kein Adapter konfiguriert.', file=sys.stderr)
        return 1
    if args.operation == 'platform-status':
        from adapter.vertrag import AdapterError
        from agent.mcp_client import platform_status

        try:
            result = platform_status(config['adapters'][args.platform])
            if result['status']['platform'] != args.platform:
                raise AdapterError('invalid_response')
        except AdapterError as error:
            print(f'Adapterfehler ({error.code}): {error}', file=sys.stderr)
            return 1
        platform_result(result, args.json)
        return 0
    if args.operation == 'status' and args.run_id is None:
        return overview(config, args.platform, args.json, args.all)
    if args.operation == 'create':
        if args.parallel > args.count or (args.parallel > 1 and args.platform != 'kubevirt'):
            print('--parallel darf bei KubeVirt höchstens --count sein und muss bei AWS 1 sein.',
                  file=sys.stderr)
            return 1
        if not args.definition.is_file():
            print(f'Ungültig: Die Datei {args.definition} wurde nicht gefunden.', file=sys.stderr)
            return 1
        try:
            model = load_model(args.definition)
        except ModelValidationError as error:
            for message in error.errors:
                print(f'Ungültig: {message}', file=sys.stderr)
            return 1

    from adapter.kubevirt_manifest import validate_id
    from adapter.vertrag import AdapterError
    from agent.lebenszyklus import create, status, reset, delete
    from agent.zustand import StateError, StateStore

    count = args.count
    operation_prefix = getattr(args, 'operation_id', None)
    suffixes = [''] if count == 1 else [f'-{index}' for index in range(1, count + 1)]
    for label, value in (('Ungültiger Name', args.run_id),
                         ('Ungültige Operationskennung', operation_prefix)):
        if value is None:
            continue
        try:
            validate_id(value + suffixes[-1])
        except AdapterError:
            note = ' mit Nummernzusatz' if count > 1 else ''
            print(f'{label}{note} "{value + suffixes[-1]}". {ID_RULE}', file=sys.stderr)
            return 1

    if args.operation == 'create' and args.platform == 'aws':
        # Grenzen des AWS-Instanztyps prüfen, bevor ein Lauf gespeichert oder ein Platz belegt wird.
        from adapter.aws import check_model
        from adapter.kubevirt_manifest import resource_name

        try:
            check_model(resource_name(args.run_id + suffixes[-1]), model['vm'])
        except AdapterError as error:
            print(f'Fehler ({error.code}): {error} Es wurde nichts erstellt und nichts gespeichert.',
                  file=sys.stderr)
            return 1
    if args.operation == 'create' and args.parallel > 1:
        return create_parallel(args, config, model, suffixes)

    result = 0
    for suffix in suffixes:
        run_id = args.run_id + suffix
        platform = getattr(args, 'platform', None)
        run_config = config
        if args.operation != 'create' and args.config is None and platform is None:
            # Ohne --platform gilt die Standardkonfiguration der gespeicherten Plattform.
            stored = stored_platform(config, run_id)
            if stored not in (None, 'kubevirt'):
                path = default_config_path(stored)
                try:
                    run_config = load_config(path)
                except ConfigurationError as error:
                    print(f'Konfigurationsfehler: {error} Standardkonfiguration: {path}. '
                          'Eine andere Datei kann mit --config gewählt werden.', file=sys.stderr)
                    result = 1
                    continue
        try:
            if args.operation != 'create' and platform:
                if not config['stateFile'].is_file():
                    raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
                record = StateStore(config['stateFile']).get(run_id)
                if record['platform'] != platform:
                    raise StateError('Die gewählte Plattform passt nicht zum gespeicherten Lauf.')
            if args.operation == 'status':
                status(run_config, run_id)
                continue
            operation_id = operation_prefix + suffix if operation_prefix else uuid.uuid4().hex
            if args.operation == 'create':
                create(config, run_id, operation_id, args.platform, model, args.timeout_seconds)
            elif args.operation == 'delete':
                delete(run_config, run_id, operation_id, args.timeout_seconds)
            else:
                reset(run_config, run_id, operation_id, args.timeout_seconds)
        except (AdapterError, StateError) as error:
            label = f'Fehler ({error.code})' if isinstance(error, AdapterError) else 'Fehler'
            if count > 1:
                label = f'{label} für {run_id}'
            if (isinstance(error, StateError) and args.operation != 'create'
                    and not is_stored(config, run_id)):
                error = (f'Unter dem Namen "{run_id}" ist keine Umgebung gespeichert. '
                         'Die vorhandenen Lernumgebungen zeigt status ohne --name.')
            print(f'{label}: {error}', file=sys.stderr)
            result = 1
            if args.operation == 'create':
                break
        except KeyboardInterrupt:
            print('Operation unterbrochen; gespeicherten Zustand prüfen.', file=sys.stderr)
            return 130
    return result


def is_stored(config, run_id):
    """Nur lesend prüfen, ob der Name (intern Laufkennung) bekannt ist."""
    from agent.zustand import read_runs

    try:
        return any(run['run_id'] == run_id for run in read_runs(config['stateFile']))
    except sqlite3.Error:
        return True  # Im Zweifel bleibt die ursprüngliche Meldung stehen.


def stored_platform(config, run_id):
    """Plattform eines gespeicherten Laufs nur lesend ermitteln."""
    from agent.zustand import read_runs

    try:
        return next((run['platform'] for run in read_runs(config['stateFile'])
                     if run['run_id'] == run_id), None)
    except sqlite3.Error:
        return None


def overview(config, platform, json_output, show_all=False):
    """Gespeicherte Läufe nur lesend auflisten; ohne Plattformaufruf und ohne neue Datenbank."""
    from agent.zustand import read_runs

    try:
        runs = read_runs(config['stateFile'])
    except sqlite3.Error:
        print('Fehler: Der Zustandsspeicher ist momentan nicht lesbar.', file=sys.stderr)
        return 1
    if platform:
        runs = [run for run in runs if run['platform'] == platform]
    run_overview(runs, json_output, show_all)
    return 0


def create_parallel(args, config, model, suffixes):
    from adapter.vertrag import AdapterError
    from agent.lebenszyklus import create
    from agent.zustand import StateError

    cancel = Event()

    def create_one(suffix):
        run_id = args.run_id + suffix
        operation_id = args.operation_id + suffix if args.operation_id else uuid.uuid4().hex
        with output_mode(args.json, prefix=run_id):
            try:
                create(config, run_id, operation_id, args.platform, model,
                       args.timeout_seconds, cancel=cancel)
            except (AdapterError, StateError) as error:
                label = f'Fehler ({error.code})' if isinstance(error, AdapterError) else 'Fehler'
                sys.stderr.write(f'{label} für {run_id}: {error}\n')
                return False
            except KeyboardInterrupt:
                return False
        return True

    remaining = iter(suffixes)
    failed = False
    executor = ThreadPoolExecutor(max_workers=args.parallel)
    try:
        active = {executor.submit(create_one, next(remaining)) for _ in range(args.parallel)}
        while active:
            done, active = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                if not future.result():
                    failed = True
            if not failed:
                for suffix in (next(remaining, None) for _ in done):
                    if suffix is not None:
                        active.add(executor.submit(create_one, suffix))
    except KeyboardInterrupt:
        cancel.set()
        print('Operation unterbrochen. Die laufenden Aufträge werden angehalten und gesichert; '
              'das dauert einige Sekunden. Bitte warten.', file=sys.stderr)
        try:
            executor.shutdown(wait=True, cancel_futures=True)
        except KeyboardInterrupt:
            # Ein zweiter Abbruch beendet sofort. Offene Aufträge übernimmt der nächste Befehl.
            print('Abbruch erzwungen. Zustand mit status prüfen; unvollständige Maschinen '
                  'mit delete entfernen.', file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(130)
        print('Gespeicherten Zustand mit status prüfen.', file=sys.stderr)
        return 130
    executor.shutdown(wait=True)
    return int(failed)

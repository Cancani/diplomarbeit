"""Lernumgebungen mit persistentem Zustand und Plattformadaptern steuern."""
import argparse
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
RUN_ID_HELP = 'Laufkennung: Name der Lernumgebung, bleibt für alle Befehle gleich'
OPERATION_ID_HELP = ('Operationskennung des Auftrags; wird ohne Angabe erzeugt und nur '
                     'angegeben, um einen unterbrochenen Auftrag fortzusetzen')
ID_RULE = ('Erlaubt sind Kleinbuchstaben, Ziffern und einzelne Bindestriche, '
           'höchstens 63 Zeichen. Beispiel: demo-01')
EXAMPLES = '''Begriffe:
  Laufkennung (--run-id)
      Name einer Lernumgebung. Sie bleibt für create, status, reset und delete gleich.
  Operationskennung (--operation-id)
      Kennung eines einzelnen Auftrags. Der Agent erzeugt sie selbst. Sie wird nur
      angegeben, um einen unterbrochenen Auftrag fortzusetzen.
  Anzahl (--count)
      Mehrere gleiche Lernumgebungen. Die Laufkennungen erhalten die Endungen -1, -2 usw.

Beispiele:
  python -m agent create modell/beispiele/referenz.yaml --platform kubevirt --run-id demo-01
  python -m agent status --platform kubevirt
  python -m agent status --platform kubevirt --run-id demo-01
  python -m agent reset --platform kubevirt --run-id demo-01
  python -m agent delete --platform kubevirt --run-id demo-01
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
            command.add_argument('--run-id', help='Laufkennung; ohne Angabe erscheint die '
                                                  'Übersicht der gespeicherten Lernumgebungen')
        else:
            command.add_argument('--run-id', required=True, help=RUN_ID_HELP)
        if name != 'create':
            command.add_argument('--platform', choices=('kubevirt', 'aws'),
                                 help='Standardkonfiguration wählen und Laufplattform prüfen')
        if name in ('create', 'status', 'delete'):
            command.add_argument('--count', type=vm_count, default=1,
                                 help='Anzahl gleicher Lernumgebungen; ab 2 erhalten die '
                                      'Laufkennungen die Endungen -1, -2 usw. (Standard: 1)')
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
    if args.config is None and getattr(args, 'platform', None) is None:
        parser.error('Bitte --platform oder eine Konfigurationsdatei mit --config angeben.')
    if args.operation == 'status' and args.run_id is None and args.count != 1:
        parser.error('--count benötigt eine Laufkennung mit --run-id.')
    with output_mode(args.json):
        return run(args)


def run(args):
    source = args.config
    try:
        if source is None:
            source = default_config_path(getattr(args, 'platform', None))
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
        return overview(config, args.platform, args.json)
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
    for label, value in (('Laufkennung', args.run_id), ('Operationskennung', operation_prefix)):
        if value is None:
            continue
        try:
            validate_id(value + suffixes[-1])
        except AdapterError:
            note = ' mit Nummernzusatz' if count > 1 else ''
            print(f'Ungültige {label}{note} "{value + suffixes[-1]}". {ID_RULE}', file=sys.stderr)
            return 1

    if args.operation == 'create' and args.parallel > 1:
        return create_parallel(args, config, model, suffixes)

    result = 0
    for suffix in suffixes:
        run_id = args.run_id + suffix
        try:
            platform = getattr(args, 'platform', None)
            if args.operation != 'create' and platform:
                if not config['stateFile'].is_file():
                    raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
                record = StateStore(config['stateFile']).get(run_id)
                if record['platform'] != platform:
                    raise StateError('Die gewählte Plattform passt nicht zum gespeicherten Lauf.')
            if args.operation == 'status':
                status(config, run_id)
                continue
            operation_id = operation_prefix + suffix if operation_prefix else uuid.uuid4().hex
            if args.operation == 'create':
                create(config, run_id, operation_id, args.platform, model, args.timeout_seconds)
            elif args.operation == 'delete':
                delete(config, run_id, operation_id, args.timeout_seconds)
            else:
                reset(config, run_id, operation_id, args.timeout_seconds)
        except (AdapterError, StateError) as error:
            label = f'Fehler ({error.code})' if isinstance(error, AdapterError) else 'Fehler'
            if count > 1:
                label = f'{label} für {run_id}'
            if (isinstance(error, StateError) and args.operation != 'create'
                    and not is_stored(config, run_id)):
                error = (f'Für die Laufkennung "{run_id}" ist keine Umgebung gespeichert. '
                         'Die gespeicherten Lernumgebungen zeigt status ohne --run-id.')
            print(f'{label}: {error}', file=sys.stderr)
            result = 1
            if args.operation == 'create':
                break
        except KeyboardInterrupt:
            print('Operation unterbrochen; gespeicherten Zustand prüfen.', file=sys.stderr)
            return 130
    return result


def is_stored(config, run_id):
    """Nur lesend prüfen, ob die Laufkennung bekannt ist."""
    from agent.zustand import read_runs

    try:
        return any(run['run_id'] == run_id for run in read_runs(config['stateFile']))
    except sqlite3.Error:
        return True  # Im Zweifel bleibt die ursprüngliche Meldung stehen.


def overview(config, platform, json_output):
    """Gespeicherte Läufe nur lesend auflisten; ohne Plattformaufruf und ohne neue Datenbank."""
    from agent.zustand import read_runs

    try:
        runs = read_runs(config['stateFile'])
    except sqlite3.Error:
        print('Fehler: Der Zustandsspeicher ist momentan nicht lesbar.', file=sys.stderr)
        return 1
    if platform:
        runs = [run for run in runs if run['platform'] == platform]
    run_overview(runs, json_output)
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
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
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
            print('Operation unterbrochen; gespeicherten Zustand prüfen.', file=sys.stderr)
            return 130
    return int(failed)

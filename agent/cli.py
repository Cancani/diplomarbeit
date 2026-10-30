"""Aufträge einlesen und prüfen; Lebenszyklussteuerung folgt separat."""
import argparse
import json
from pathlib import Path
import sys

from modell.validierung import load_model, ModelValidationError
from agent.konfiguration import ConfigurationError, load_config


def build_parser():
    parser = argparse.ArgumentParser(
        description='Lernumgebungen erstellen, prüfen, zurücksetzen und löschen.')
    parser.add_argument('--config', type=Path, required=True,
                        help='YAML-Datei der Agent-Konfiguration')
    commands = parser.add_subparsers(dest='operation', required=True)
    probe = commands.add_parser('platform-status', help='Plattform über MCP lesend prüfen')
    probe.add_argument('--platform', required=True, choices=('kubevirt', 'aws'))
    descriptions = {
        'create': 'Lernumgebung aus einer YAML-Definition erstellen',
        'status': 'Zustand einer Lernumgebung abfragen',
        'reset': 'Lernumgebung aus dem gespeicherten Modell neu erstellen',
        'delete': 'Lernumgebung vollständig entfernen',
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description, description=description)
        command.add_argument('--run-id', required=True, help='Kennung des Laufs')
        if name == 'create':
            command.add_argument('definition', type=Path, help='YAML-Datei der Lernumgebung')
            command.add_argument('--platform', required=True, choices=('kubevirt', 'aws'),
                                 help='Zielplattform')
    return parser


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigurationError as error:
        print(f'Konfigurationsfehler: {error}', file=sys.stderr)
        return 1
    if args.operation == 'platform-status':
        from adapter.vertrag import AdapterError
        from agent.mcp_client import platform_status

        if args.platform not in config['adapters']:
            print(f'Für die Zielplattform {args.platform} ist kein Adapter konfiguriert.',
                  file=sys.stderr)
            return 1
        try:
            result = platform_status(config['adapters'][args.platform])
            if result['status']['platform'] != args.platform:
                raise AdapterError('invalid_response')
        except AdapterError as error:
            print(f'Adapterfehler ({error.code}): {error}', file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.operation == 'create':
        if args.platform not in config['adapters']:
            print(f'Für die Zielplattform {args.platform} ist kein Adapter konfiguriert.',
                  file=sys.stderr)
            return 1
        try:
            load_model(args.definition)
        except ModelValidationError as error:
            for message in error.errors:
                print(f'Ungültig: {message}', file=sys.stderr)
            return 1
    print(f'{args.operation}: Die Lebenszyklussteuerung ist noch nicht implementiert.',
          file=sys.stderr)
    return 1

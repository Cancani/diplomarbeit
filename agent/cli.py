"""Aufträge einlesen und prüfen; Lebenszyklussteuerung folgt separat."""
import argparse
from pathlib import Path
import sys

from modell.validierung import load_model, ModelValidationError


def build_parser():
    parser = argparse.ArgumentParser(
        description='Lernumgebungen erstellen, prüfen, zurücksetzen und löschen.')
    commands = parser.add_subparsers(dest='operation', required=True)
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
    if args.operation == 'create':
        try:
            load_model(args.definition)
        except ModelValidationError as error:
            for message in error.errors:
                print(f'Ungültig: {message}', file=sys.stderr)
            return 1
    print(f'{args.operation}: Die Lebenszyklussteuerung ist noch nicht implementiert.',
          file=sys.stderr)
    return 1

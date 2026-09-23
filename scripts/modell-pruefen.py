#!/usr/bin/env python3
"""Lokale Modellvalidierung ohne Infrastrukturzugriff."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modell.validierung import load_model, ModelValidationError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('definition', type=Path, help='YAML-Datei der Lernumgebung')
    args = parser.parse_args()
    try:
        document = load_model(args.definition)
    except ModelValidationError as error:
        for message in error.errors:
            print(f'Ungueltig: {message}', file=sys.stderr)
        return 1
    print(f'Gueltig: {document["name"]} (Modellversion {document["modelVersion"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())

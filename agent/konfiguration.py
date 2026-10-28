"""Externe Agent-Konfiguration prüfen, ohne Dateien oder Prozesse anzulegen."""
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

from modell.validierung import ModelLoader


ADAPTER_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['command', 'args', 'timeoutSeconds'],
    'properties': {
        'command': {'type': 'string', 'pattern': r'\S'},
        'args': {'type': 'array', 'items': {'type': 'string'}},
        'timeoutSeconds': {'type': 'integer', 'minimum': 1},
    },
}

SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'required': ['stateFile', 'adapters'],
    'properties': {
        'stateFile': {'type': 'string', 'pattern': r'\S'},
        'adapters': {
            'type': 'object',
            'additionalProperties': False,
            'minProperties': 1,
            'properties': {'kubevirt': ADAPTER_SCHEMA, 'aws': ADAPTER_SCHEMA},
        },
    },
}


class ConfigurationError(ValueError):
    """Verständlicher Konfigurationsfehler ohne eingegebene Werte."""


def load_config(path):
    try:
        source = Path(path).expanduser().resolve()
        document = yaml.load(source.read_text(encoding='utf-8-sig'), Loader=ModelLoader)
    except (OSError, RuntimeError) as error:
        raise ConfigurationError('Konfigurationsdatei konnte nicht gelesen werden.') from error
    except UnicodeError as error:
        raise ConfigurationError('Die Konfiguration muss UTF-8-kodiert sein.') from error
    except yaml.YAMLError as error:
        raise ConfigurationError('Die Konfiguration enthält ungültiges oder mehrdeutiges YAML.') from error

    errors = list(Draft202012Validator(SCHEMA).iter_errors(document))
    if errors:
        error = errors[0]
        field = '$' + ''.join(f'[{part}]' if isinstance(part, int) else f'.{part}'
                              for part in error.absolute_path)
        raise ConfigurationError(
            f'Ungültige Konfiguration bei {field}. '
            'Prüfe Pflichtfelder, Feldnamen, Datentypen und positive Zeitgrenzen.')

    try:
        state_file = Path(document['stateFile']).expanduser()
        if not state_file.is_absolute():
            state_file = source.parent / state_file
        document['stateFile'] = state_file.resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise ConfigurationError('Der Zustandspfad ist ungültig.') from error
    return document

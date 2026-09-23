"""Datei und Schema lokal pruefen; keine Ressourcen erzeugen."""
import base64
import binascii
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker
import yaml
from yaml.constructor import ConstructorError


SCHEMA_PATH = Path(__file__).with_name('lernumgebung-v1.schema.json')


class ModelValidationError(ValueError):
    def __init__(self, errors):
        self.errors = tuple(errors)
        super().__init__('; '.join(self.errors))


class ModelLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ConstructorError(None, None, 'YAML-Aliase sind nicht erlaubt', self.peek_event().start_mark)
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConstructorError(None, None, 'Feldnamen muessen Text sein', key_node.start_mark)
            if key in result:
                raise ConstructorError(None, None, 'Doppeltes YAML-Feld', key_node.start_mark)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


FORMATS = FormatChecker()


@FORMATS.checks('ssh-ed25519')
def is_ed25519_public_key(value):
    if not isinstance(value, str):
        return True  # Die Typpruefung uebernimmt das Schema.
    if not re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/]{68}(?: [^\r\n]+)?', value):
        return False
    try:
        data = base64.b64decode(value.split(' ', 2)[1], validate=True)
    except (ValueError, binascii.Error):
        return False
    prefix = b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20'
    return len(data) == len(prefix) + 32 and data.startswith(prefix)


def error_text(error):
    path = '$' + ''.join(f'[{part}]' if isinstance(part, int) else f'.{part}'
                         for part in error.absolute_path)
    kind, value = error.validator, error.validator_value
    if kind == 'required':
        missing = sorted(set(value) - error.instance.keys())
        message = 'Pflichtfelder fehlen: ' + ', '.join(missing)
    elif kind == 'additionalProperties':
        message = 'Unbekannte Felder: ' + ', '.join(sorted(set(error.instance) - error.schema['properties'].keys()))
    elif kind == 'minimum':
        message = f'Muss mindestens {value} sein.'
    elif kind == 'type':
        message = f'Erwarteter Datentyp: {value}.'
    elif kind == 'const':
        message = f'Fuer Modellversion 1.0 ist {json.dumps(value, ensure_ascii=False)} vorgeschrieben.'
    elif kind == 'format':
        message = 'Ein oeffentlicher Ed25519-Schluessel im OpenSSH-Format ist erforderlich.'
    elif kind == 'minItems':
        message = f'Mindestens {value} Eintrag ist erforderlich.'
    elif kind == 'uniqueItems':
        message = 'Doppelte Eintraege sind nicht erlaubt.'
    elif kind == 'pattern':
        message = 'Das Textformat ist ungueltig.'
    else:
        message = f'Schemaregel {kind} verletzt.'
    return f'{path}: {message}'


def validate_model(document):
    """Gibt bei Erfolg das Modell zurueck, sonst strukturierte Fehler."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FORMATS)
    errors = sorted(set(error_text(error) for error in validator.iter_errors(document)))
    if errors:
        raise ModelValidationError(errors)
    return document


def load_model(path):
    try:
        with Path(path).open('r', encoding='utf-8-sig') as stream:
            document = yaml.load(stream, Loader=ModelLoader)
    except OSError as error:
        raise ModelValidationError(['Datei konnte nicht gelesen werden.']) from error
    except UnicodeError as error:
        raise ModelValidationError(['Die Datei muss UTF-8-kodiert sein.']) from error
    except yaml.YAMLError as error:
        mark = getattr(error, 'problem_mark', None)
        position = f' in Zeile {mark.line + 1}, Spalte {mark.column + 1}' if mark else ''
        reason = error.problem if isinstance(error, ConstructorError) and error.problem in (
            'YAML-Aliase sind nicht erlaubt', 'Feldnamen muessen Text sein', 'Doppeltes YAML-Feld') else 'Ungueltiges YAML'
        raise ModelValidationError([reason + position + '.']) from error
    try:
        json.dumps(document, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ModelValidationError(['Nur JSON-kompatible YAML-Werte sind erlaubt.']) from error
    return validate_model(document)

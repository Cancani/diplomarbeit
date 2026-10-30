"""Erster Adaptervertrag: platform_status() liest ohne Ressourcenänderung.

Erfolg: {ok: true, status: {...}}. Fehler: {ok: false, error: Fehlercode}.
Ein Plattformstatus bestätigt keine HTTP-Bereitschaft einer Lernumgebung.
"""
from jsonschema import Draft202012Validator


ERRORS = {
    'command_not_found': 'Das Kubernetes-Werkzeug wurde nicht gefunden.',
    'platform_error': 'Die Clusterabfrage ist fehlgeschlagen. Prüfe den lokalen Clusterzugang.',
    'timeout': 'Die Zeitgrenze für die Abfrage wurde überschritten.',
    'invalid_response': 'Die Adapterantwort entspricht nicht dem vereinbarten Format.',
    'transport_error': 'Der MCP-Adapter konnte nicht gestartet oder erreicht werden.',
}

MACHINE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['name', 'namespace', 'id', 'state'],
    'properties': {key: {'type': 'string', 'minLength': 1}
                   for key in ['name', 'namespace', 'id', 'state']},
}

STATUS_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['platform', 'nodes', 'kubevirtPhase', 'virtualMachines', 'virtualMachineInstances'],
    'properties': {
        'platform': {'const': 'kubevirt'},
        'nodes': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['name', 'ready'],
            'properties': {'name': {'type': 'string', 'minLength': 1}, 'ready': {'type': 'boolean'}},
        }},
        'kubevirtPhase': {'type': 'string', 'minLength': 1},
        'virtualMachines': {'type': 'array', 'items': MACHINE_SCHEMA},
        'virtualMachineInstances': {'type': 'array', 'items': MACHINE_SCHEMA},
    },
}

RESPONSE_SCHEMA = {'oneOf': [
    {'type': 'object', 'additionalProperties': False, 'required': ['ok', 'status'],
     'properties': {'ok': {'const': True}, 'status': STATUS_SCHEMA}},
    {'type': 'object', 'additionalProperties': False, 'required': ['ok', 'error'],
     'properties': {'ok': {'const': False}, 'error': {'enum': list(ERRORS)}}},
]}


class AdapterError(ValueError):
    def __init__(self, code):
        self.code = code if code in ERRORS else 'invalid_response'
        super().__init__(ERRORS[self.code])


def read_status_response(response):
    if not Draft202012Validator(RESPONSE_SCHEMA).is_valid(response):
        raise AdapterError('invalid_response')
    if not response['ok']:
        raise AdapterError(response['error'])
    return response['status']

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
    'invalid_request': 'Modell oder Auftragskennungen sind ungültig.',
    'resource_conflict': 'Vorhandene Ressourcen oder ihre Kennzeichnungen widersprechen dem Auftrag.',
    'capacity_limit': 'Die Obergrenze von 30 verwalteten VMs ist erreicht.',
    'storage_unverified': 'Die Zuordnung oder Entfernung des lokalen Datenträgers ist nicht bestätigt.',
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


RESOURCE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['kind', 'name', 'resource_id', 'scope'],
    'properties': {key: {'type': 'string', **({'minLength': 1} if key != 'scope' else {})}
                   for key in ['kind', 'name', 'resource_id', 'scope']},
}
RESOURCE_SCHEMA['properties']['details'] = {
    'type': 'object', 'additionalProperties': False,
    'properties': {key: {'type': 'string', 'minLength': 1}
                   for key in ['claimUid', 'claimName', 'hostPath', 'nodeName']},
}
RESOURCE_SCHEMA['properties']['details']['properties']['pathSource'] = {'enum': ['api', 'provisioner-name']}
CREATE_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['complete', 'resources'],
    'properties': {'complete': {'type': 'boolean'},
                   'resources': {'type': 'array', 'items': RESOURCE_SCHEMA}},
}
RUN_STATUS_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['resources', 'vmState', 'vmiPhase', 'vmReady', 'modelHash', 'httpUrl', 'sshHost', 'sshPort'],
    'properties': {
        'resources': {'type': 'array', 'items': RESOURCE_SCHEMA},
        'vmState': {'type': 'string'}, 'vmiPhase': {'type': 'string'}, 'vmReady': {'type': 'boolean'},
        'modelHash': {'type': ['string', 'null']}, 'httpUrl': {'type': ['string', 'null']},
        'sshHost': {'type': ['string', 'null']}, 'sshPort': {'type': ['integer', 'null']},
    },
}
DELETE_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['complete', 'resources', 'removed'],
    'properties': {'complete': {'type': 'boolean'},
                   'resources': {'type': 'array', 'items': RESOURCE_SCHEMA},
                   'removed': {'type': 'array', 'items': RESOURCE_SCHEMA}},
}


def read_result(response, schema):
    if not isinstance(response, dict) or type(response.get('ok')) is not bool:
        raise AdapterError('invalid_response')
    if not response['ok']:
        if set(response) != {'ok', 'error'} or not isinstance(response['error'], str) or response['error'] not in ERRORS:
            raise AdapterError('invalid_response')
        raise AdapterError(response['error'])
    if set(response) != {'ok', 'data'} or not Draft202012Validator(schema).is_valid(response['data']):
        raise AdapterError('invalid_response')
    return response['data']

"""Adaptervertrag: Fehlercodes und Antwortformate zwischen Agent und Adaptern.

Erfolg: {ok: true, status: {...}} oder {ok: true, data: {...}}.
Fehler: {ok: false, error: Fehlercode}.
Ein Plattformstatus bestätigt keine HTTP-Bereitschaft einer Lernumgebung.
"""
from jsonschema import Draft202012Validator


ERRORS = {
    'command_not_found': 'Das Kubernetes-Werkzeug wurde nicht gefunden.',
    'aws_cli_unavailable': 'Die AWS CLI wurde nicht gefunden.',
    'aws_query_failed': 'Der AWS-Aufruf ist fehlgeschlagen. Prüfe das AWS-Profil, die Lab-Sitzung und die Berechtigungen.',
    'aws_launch_unconfigured': 'Für den EC2-Start fehlen Konto, VPC, Subnetz oder HTTP-Quelladresse in der Adapterkonfiguration.',
    'aws_model_unsupported': 'Der EC2-Adapter unterstützt t3.small mit bis zu 100 GiB und maximal 16 KiB Cloud-init-Daten.',
    'aws_image_unavailable': 'Das EC2-Abbild für die Neuerstellung ist nicht verfügbar.',
    'platform_error': 'Die Clusterabfrage ist fehlgeschlagen. Prüfe den lokalen Clusterzugang.',
    'timeout': 'Die Zeitgrenze für die Abfrage wurde überschritten.',
    'invalid_response': 'Die Adapterantwort entspricht nicht dem vereinbarten Format.',
    'transport_error': 'Der MCP-Adapter konnte nicht gestartet oder erreicht werden.',
    'invalid_request': 'Modell oder Auftragskennungen sind ungültig.',
    'resource_conflict': 'Vorhandene Ressourcen oder ihre Kennzeichnungen widersprechen dem Auftrag.',
    'capacity_limit': 'Die Obergrenze von 30 verwalteten VMs ist erreicht.',
    'storage_unverified': 'Die Zuordnung oder Entfernung des lokalen Datenträgers ist nicht bestätigt.',
}

TEXT = {'type': 'string', 'minLength': 1}
OPTIONAL_TEXT = {'type': ['string', 'null']}


def _object(properties, optional=()):
    schema = {'type': 'object', 'additionalProperties': False, 'properties': properties}
    required = [key for key in properties if key not in optional]
    if required:
        schema['required'] = required
    return schema


def _list(items):
    return {'type': 'array', 'items': items}


MACHINE_SCHEMA = _object({'name': TEXT, 'namespace': TEXT, 'id': TEXT, 'state': TEXT})

STATUS_SCHEMA = _object({
    'platform': {'const': 'kubevirt'},
    'nodes': _list(_object({'name': TEXT, 'ready': {'type': 'boolean'}})),
    'kubevirtPhase': TEXT,
    'virtualMachines': _list(MACHINE_SCHEMA),
    'virtualMachineInstances': _list(MACHINE_SCHEMA),
})

AWS_STATUS_SCHEMA = _object({
    'platform': {'const': 'aws'},
    'region': TEXT,
    'instances': _list(_object({
        'id': {'type': 'string', 'pattern': '^i-[0-9a-f]+$'},
        'state': {'enum': ['pending', 'running', 'shutting-down', 'terminated', 'stopping', 'stopped']},
    })),
})

RESPONSE_SCHEMA = {'oneOf': [
    _object({'ok': {'const': True}, 'status': {'oneOf': [STATUS_SCHEMA, AWS_STATUS_SCHEMA]}}),
    _object({'ok': {'const': False}, 'error': {'enum': list(ERRORS)}}),
]}

RESOURCE_SCHEMA = _object({
    'kind': TEXT, 'name': TEXT, 'resource_id': TEXT, 'scope': {'type': 'string'},
    'details': _object({'claimUid': TEXT, 'claimName': TEXT, 'hostPath': TEXT, 'nodeName': TEXT,
                        'pathSource': {'enum': ['api', 'provisioner-name']}},
                       optional=('claimUid', 'claimName', 'hostPath', 'nodeName', 'pathSource')),
}, optional=('details',))
CREATE_SCHEMA = _object({'complete': {'type': 'boolean'}, 'resources': _list(RESOURCE_SCHEMA)})
RUN_STATUS_SCHEMA = _object({
    'resources': _list(RESOURCE_SCHEMA),
    'vmState': {'type': 'string'}, 'vmiPhase': {'type': 'string'}, 'vmReady': {'type': 'boolean'},
    'modelHash': OPTIONAL_TEXT, 'httpUrl': OPTIONAL_TEXT,
    'sshHost': OPTIONAL_TEXT, 'sshPort': {'type': ['integer', 'null']},
})
DELETE_SCHEMA = _object({'complete': {'type': 'boolean'}, 'resources': _list(RESOURCE_SCHEMA),
                         'removed': _list(RESOURCE_SCHEMA)})
RESET_CHECK_SCHEMA = {'type': 'object', 'maxProperties': 0}


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

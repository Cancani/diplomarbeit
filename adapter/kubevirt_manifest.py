"""Plattformdetails für genau eine VM je Modellversion 1.0."""
import hashlib
import re
from copy import deepcopy

from adapter.cloud_init import cloud_init
from adapter.vertrag import AdapterError
from modell.snapshot import encode_snapshot


NAMESPACE = 'diplomarbeit-agent'
MANAGER = 'diplomarbeit-agent'
MAX_VMS = 30
IMAGE_URL = 'https://cloud-images.ubuntu.com/noble/20260911/noble-server-cloudimg-amd64.img'
IMAGE_SHA256 = '612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354'


def validate_id(value):
    if not isinstance(value, str) or len(value) > 63 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise AdapterError('invalid_request')


def resource_name(run_id):
    validate_id(run_id)
    return 'da-' + hashlib.sha256(run_id.encode('utf-8')).hexdigest()[:24]


def labels(run_id=None, operation_id=None):
    result = {'app.kubernetes.io/managed-by': MANAGER}
    if run_id is not None:
        validate_id(run_id)
        result['diplomarbeit/run'] = run_id
    if operation_id is not None:
        validate_id(operation_id)
        result['diplomarbeit/operation'] = operation_id
    return result


def infrastructure():
    return [
        {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': NAMESPACE, 'labels': labels()}},
        {'apiVersion': 'v1', 'kind': 'ResourceQuota',
         'metadata': {'name': 'vm-limit', 'namespace': NAMESPACE, 'labels': labels()},
         'spec': {'hard': {'count/virtualmachines.kubevirt.io': str(MAX_VMS),
                           'count/virtualmachineinstances.kubevirt.io': str(MAX_VMS)}}},
    ]


def manifests(run_id, operation_id, model):
    _, digest = encode_snapshot(model)
    name = resource_name(run_id)
    tags = labels(run_id, operation_id)
    vm = model['vm']
    metadata = {'name': name, 'namespace': NAMESPACE, 'labels': tags,
                'annotations': {'diplomarbeit/model-sha256': digest,
                                'diplomarbeit/image-sha256-publisher': IMAGE_SHA256}}
    machine = {
        'apiVersion': 'kubevirt.io/v1', 'kind': 'VirtualMachine', 'metadata': metadata,
        'spec': {
            'runStrategy': 'Always',
            'dataVolumeTemplates': [{'metadata': {'name': name + '-disk', 'labels': tags}, 'spec': {
                'storage': {'storageClassName': 'microk8s-hostpath', 'accessModes': ['ReadWriteOnce'],
                            'volumeMode': 'Filesystem', 'resources': {'requests': {
                                'storage': str(int(vm['resources']['minDiskGiB'])) + 'Gi'}}},
                'source': {'http': {'url': IMAGE_URL}},
            }}],
            'template': {'metadata': {'labels': tags}, 'spec': {
                'terminationGracePeriodSeconds': 30,
                'domain': {
                    'cpu': {'cores': int(vm['resources']['minVcpus']), 'sockets': 1, 'threads': 1},
                    'memory': {'guest': str(int(vm['resources']['minMemoryMiB'])) + 'Mi'},
                    'devices': {
                        'disks': [{'name': n, 'disk': {'bus': 'virtio'}} for n in ['rootdisk', 'cloudinit']],
                        'interfaces': [{'name': 'default', 'masquerade': {},
                                        'ports': [{'name': 'ssh', 'port': 22}, {'name': 'http', 'port': 8080}]}],
                    },
                },
                'networks': [{'name': 'default', 'pod': {}}],
                'volumes': [{'name': 'rootdisk', 'dataVolume': {'name': name + '-disk'}},
                            {'name': 'cloudinit', 'cloudInitNoCloud': {
                                'userData': cloud_init(name, vm)}}],
            }},
        },
    }
    service = {'apiVersion': 'v1', 'kind': 'Service', 'metadata': deepcopy(metadata),
               'spec': {'type': 'NodePort', 'selector': dict(tags), 'ports': [
                   {'name': 'ssh', 'port': 22, 'targetPort': 22, 'protocol': 'TCP'},
                   {'name': 'http', 'port': 8080, 'targetPort': 8080, 'protocol': 'TCP'},
               ]}}
    return [machine, service]

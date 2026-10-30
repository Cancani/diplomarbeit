"""Laufbezogener Abbau mit UID-Bedingungen und Speicherabschluss."""
from pathlib import Path
import socket
import time
from urllib.parse import quote

from jsonschema import Draft202012Validator

from adapter.kubevirt_manifest import NAMESPACE, labels, resource_name, validate_id
from adapter.vertrag import AdapterError, RESOURCE_SCHEMA


RESOURCE_APIS = {
    'VirtualMachine': ('/apis/kubevirt.io/v1', 'virtualmachines'),
    'VirtualMachineInstance': ('/apis/kubevirt.io/v1', 'virtualmachineinstances'),
    'Pod': ('/api/v1', 'pods'),
    'DataVolume': ('/apis/cdi.kubevirt.io/v1beta1', 'datavolumes'),
    'PersistentVolumeClaim': ('/api/v1', 'persistentvolumeclaims'),
    'Service': ('/api/v1', 'services'),
    'EndpointSlice': ('/apis/discovery.k8s.io/v1', 'endpointslices'),
    'PersistentVolume': ('/api/v1', 'persistentvolumes'),
}


def storage_details(pv, pvc, node_name=None):
    details = {'claimUid': pvc['metadata']['uid']}
    path = pv.get('spec', {}).get('hostPath', {}).get('path')
    if path:
        details['hostPath'] = path
        terms = pv.get('spec', {}).get('nodeAffinity', {}).get('required', {}).get('nodeSelectorTerms', [])
        nodes = {value for term in terms for match in term.get('matchExpressions', [])
                 if match.get('key') == 'kubernetes.io/hostname' and match.get('operator') == 'In'
                 for value in match.get('values', [])}
        if len(nodes) == 1:
            details['nodeName'] = next(iter(nodes))
        elif node_name:
            details['nodeName'] = node_name
    return details


class KubeVirtDeletion:
    def _validate_resources(self, run_id, resources):
        name = resource_name(run_id)
        seen = {}
        for resource in resources:
            if not Draft202012Validator(RESOURCE_SCHEMA).is_valid(resource):
                raise AdapterError('invalid_request')
            kind, scope = resource['kind'], resource['scope']
            if kind not in RESOURCE_APIS or scope != ('' if kind == 'PersistentVolume' else NAMESPACE):
                raise AdapterError('resource_conflict')
            expected = name + '-disk' if kind in ('DataVolume', 'PersistentVolumeClaim') else name
            if kind in ('VirtualMachine', 'VirtualMachineInstance', 'DataVolume', 'PersistentVolumeClaim', 'Service'):
                if resource['name'] != expected:
                    raise AdapterError('resource_conflict')
            key = kind, scope, resource['name']
            if key in seen and seen[key] != resource['resource_id']:
                raise AdapterError('resource_conflict')
            seen[key] = resource['resource_id']

    def _local_storage_gone(self, resource):
        details = resource.get('details', {})
        if not details.get('claimUid') or not details.get('hostPath') or not details.get('nodeName'):
            raise AdapterError('storage_unverified')
        path = Path(details['hostPath'])
        if not path.is_absolute() or details['nodeName'] != socket.gethostname():
            raise AdapterError('storage_unverified')
        try:
            path.lstat()
            return False
        except FileNotFoundError:
            return True
        except OSError as error:
            raise AdapterError('storage_unverified') from error

    def _check_pv(self, resource, pv, run_id):
        details = resource.get('details', {})
        claim = pv.get('spec', {}).get('claimRef', {})
        if pv['metadata']['uid'] != resource['resource_id'] or (
                claim.get('uid'), claim.get('namespace'), claim.get('name')) != (
                details.get('claimUid'), NAMESPACE, resource_name(run_id) + '-disk'):
            raise AdapterError('resource_conflict')
        if (pv.get('spec', {}).get('persistentVolumeReclaimPolicy') != 'Delete'
                or pv.get('spec', {}).get('storageClassName') != 'microk8s-hostpath'
                or pv.get('spec', {}).get('hostPath', {}).get('path') != details.get('hostPath')):
            raise AdapterError('storage_unverified')
        self._local_storage_gone(resource)  # Prüft auch vor dem Abbau den lokalen Zugriff.

    def delete(self, run_id, operation_id, resources):
        """Ein Objekt löschen oder dessen Entfernung abwarten; niemals den PV erzwingen."""
        validate_id(operation_id)
        self._validate_resources(run_id, resources)
        deadline = time.monotonic() + self.timeout_seconds
        actual = self.status(run_id, resources)
        known = {r['resource_id']: r for r in resources}
        # Neue Folgeobjekte und PV-Metadaten müssen vor weiteren Änderungen persistent sein.
        if any(r['resource_id'] not in known or any(
                known[r['resource_id']].get('details', {}).get(k) != value
                for k, value in r.get('details', {}).items()) for r in actual['resources']):
            return {'complete': False, 'resources': actual['resources'], 'removed': []}
        for resource in resources:
            if resource['kind'] == 'PersistentVolume':
                pv = self._object('persistentvolume', resource['name'], deadline)
                if pv is not None:
                    self._check_pv(resource, pv, run_id)
                else:
                    self._local_storage_gone(resource)
        removed = []
        order = {kind: index for index, kind in enumerate(RESOURCE_APIS)}
        for resource in sorted(resources, key=lambda r: order[r['kind']]):
            kind = resource['kind']
            existing = self._object(kind, resource['name'], deadline, resource['scope'] or None)
            if existing is None:
                if kind == 'PersistentVolume' and not self._local_storage_gone(resource):
                    return {'complete': False, 'resources': actual['resources'], 'removed': removed}
                removed.append(resource)
                continue
            metadata = existing['metadata']
            if metadata['uid'] != resource['resource_id']:
                raise AdapterError('resource_conflict')
            if kind == 'PersistentVolume':
                # Der Provisioner muss zuerst den Datenträger vollständig bereinigen.
                return {'complete': False, 'resources': actual['resources'], 'removed': removed}
            if resource['resource_id'] not in {r['resource_id'] for r in actual['resources']}:
                self._owned(existing, {'metadata': {'labels': labels(run_id)}}, allow_deleting=True)
            if not metadata.get('deletionTimestamp'):
                base, plural = RESOURCE_APIS[kind]
                path = f'{base}/namespaces/{NAMESPACE}/{plural}/{quote(resource["name"], safe="")}'
                options = {'apiVersion': 'v1', 'kind': 'DeleteOptions',
                           'preconditions': {'uid': resource['resource_id']},
                           'propagationPolicy': 'Foreground'}
                try:
                    self._request('delete', ['--raw', path, '-f', '-'], deadline, options, output_json=False)
                except AdapterError:
                    # Ein Controller kann das Objekt zwischen GET und DELETE entfernt haben.
                    current = self._object(kind, resource['name'], deadline, resource['scope'] or None)
                    if current is None:
                        return {'complete': False, 'resources': actual['resources'], 'removed': [*removed, resource]}
                    if current['metadata']['uid'] != resource['resource_id']:
                        raise AdapterError('resource_conflict')
                    raise
            return {'complete': False, 'resources': actual['resources'], 'removed': removed}
        return {'complete': not actual['resources'], 'resources': actual['resources'], 'removed': removed}

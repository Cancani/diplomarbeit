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
    details = {'claimUid': pvc['metadata']['uid'], 'claimName': pvc['metadata']['name']}
    path = pv.get('spec', {}).get('hostPath', {}).get('path')
    if path:
        details['hostPath'] = path
        details['pathSource'] = 'api'
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
        for resource in resources:
            if not Draft202012Validator(RESOURCE_SCHEMA).is_valid(resource):
                raise AdapterError('invalid_request')
            kind, scope = resource['kind'], resource['scope']
            if kind not in RESOURCE_APIS or scope != ('' if kind == 'PersistentVolume' else NAMESPACE):
                raise AdapterError('resource_conflict')
            expected = {name + '-disk'} if kind in ('DataVolume', 'PersistentVolumeClaim') else {name}
            if kind == 'PersistentVolumeClaim':
                expected.add(name + '-disk-scratch')
            if kind in ('VirtualMachine', 'VirtualMachineInstance', 'DataVolume', 'PersistentVolumeClaim', 'Service'):
                if resource['name'] not in expected:
                    raise AdapterError('resource_conflict')
        # Pod- und Scratch-Namen können nach einem Neustart mit neuer UID wiederkehren.
        # Deshalb wird jede gespeicherte UID einzeln auf Abwesenheit geprüft.

    def _storage_updates(self, run_id, known, actual, deadline):
        merged = {r['resource_id']: {**r, 'details': dict(r.get('details', {}))} for r in known}
        for resource in actual:
            previous = merged.get(resource['resource_id'], {})
            merged[resource['resource_id']] = {
                **resource, 'details': {**previous.get('details', {}), **resource.get('details', {})}}
        claims = {r['resource_id']: r for r in merged.values() if r['kind'] == 'PersistentVolumeClaim'}
        updates = []
        for resource in list(merged.values()):
            if resource['kind'] != 'PersistentVolume':
                continue
            details = resource.get('details', {})
            claim = claims.get(details.get('claimUid'))
            if claim and not details.get('claimName'):
                details['claimName'] = claim['name']
            if all(details.get(k) for k in ('claimUid', 'claimName', 'hostPath', 'nodeName')):
                if details != next((r.get('details', {}) for r in known if r['resource_id'] == resource['resource_id']), {}):
                    updates.append(resource)
                continue
            pv = self._object('persistentvolume', resource['name'], deadline)
            if pv is not None:
                binding = pv.get('spec', {}).get('claimRef', {})
                claim = claims.get(binding.get('uid'))
                if (pv['metadata']['uid'] != resource['resource_id'] or claim is None
                        or (binding.get('namespace'), binding.get('name')) != (NAMESPACE, claim['name'])):
                    raise AdapterError('resource_conflict')
                resource['details'] = storage_details(pv, {'metadata': {'uid': claim['resource_id'], 'name': claim['name']}})
            else:
                # Alte Inventare können einen inzwischen entfernten CDI-Scratch-PV
                # ohne Pfad enthalten. Der MicroK8s-Provisioner verwendet den Namen
                # <Namespace>-<PVC>-<PV> unter dem PV-Verzeichnis.
                claim = next((r for r in claims.values()
                              if resource['name'] == 'pvc-' + r['resource_id']
                              and r['name'] == resource_name(run_id) + '-disk-scratch'), None)
                config = self._object('cdiconfig', 'config', deadline)
                if config is None:
                    raise AdapterError('storage_unverified')
                scratch_class = (config.get('spec', {}).get('scratchSpaceStorageClass')
                                 or config.get('status', {}).get('scratchSpaceStorageClass'))
                if not scratch_class:
                    # CDI verwendet ohne Override die Speicherklasse des Ziel-PVC.
                    target = self._object('persistentvolumeclaim', resource_name(run_id) + '-disk',
                                          deadline, NAMESPACE)
                    if (target is None or target['metadata']['uid'] not in claims
                            or claims[target['metadata']['uid']]['name'] != resource_name(run_id) + '-disk'):
                        raise AdapterError('storage_unverified')
                    scratch_class = target.get('spec', {}).get('storageClassName')
                if scratch_class != 'microk8s-hostpath':
                    raise AdapterError('storage_unverified')
                roots = set()
                for anchor in merged.values():
                    info = anchor.get('details', {})
                    if (anchor['kind'] != 'PersistentVolume'
                            or not all(info.get(k) for k in ('claimUid', 'claimName', 'hostPath', 'nodeName'))
                            or anchor['name'] != 'pvc-' + info['claimUid']):
                        continue
                    path = Path(info['hostPath'])
                    if path.name != f'{NAMESPACE}-{info["claimName"]}-{anchor["name"]}':
                        continue
                    present = self._object('persistentvolume', anchor['name'], deadline)
                    if present is not None:
                        self._check_pv(anchor, present, run_id)
                        roots.add((str(path.parent), info['nodeName']))
                if claim is None or len(roots) != 1:
                    raise AdapterError('storage_unverified')
                root, node = next(iter(roots))
                resource['details'] = {
                    'claimUid': claim['resource_id'], 'claimName': claim['name'], 'nodeName': node,
                    'hostPath': str(Path(root) / f'{NAMESPACE}-{claim["name"]}-{resource["name"]}'),
                    'pathSource': 'provisioner-name',
                }
            if not all(resource['details'].get(k) for k in ('claimUid', 'claimName', 'hostPath', 'nodeName')):
                raise AdapterError('storage_unverified')
            updates.append(resource)
        return updates

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
                details.get('claimUid'), NAMESPACE, details.get('claimName', resource_name(run_id) + '-disk')):
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
        storage_updates = self._storage_updates(run_id, resources, actual['resources'], deadline)
        # Neue Folgeobjekte und PV-Metadaten müssen vor weiteren Änderungen persistent sein.
        if storage_updates or any(r['resource_id'] not in known or any(
                known[r['resource_id']].get('details', {}).get(k) != value
                for k, value in r.get('details', {}).items()) for r in actual['resources']):
            changes = {r['resource_id']: r for r in [*actual['resources'], *storage_updates]}
            return {'complete': False, 'resources': list(changes.values()), 'removed': []}
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
                if metadata['uid'] in known and metadata['uid'] in {r['resource_id'] for r in actual['resources']}:
                    removed.append(resource)
                    continue
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

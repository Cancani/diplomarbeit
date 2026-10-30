"""Erstellung in einzelnen bestätigten Schritten und laufbezogener Bestand."""
import ipaddress
import time

from adapter.kubevirt_manifest import NAMESPACE, MAX_VMS, labels, infrastructure, manifests, resource_name
from adapter.kubevirt_provider import KubeVirtProvider
from adapter.vertrag import AdapterError


def reference(resource):
    try:
        metadata = resource['metadata']
        return {'kind': resource['kind'], 'name': metadata['name'],
                'resource_id': metadata['uid'], 'scope': metadata.get('namespace', '')}
    except (KeyError, TypeError) as error:
        raise AdapterError('invalid_response') from error


class KubeVirtLifecycle(KubeVirtProvider):
    def _object(self, kind, name, deadline, namespace=None):
        arguments = [kind.lower(), name, '--ignore-not-found']
        if namespace:
            arguments += ['-n', namespace]
        return self._request('get', arguments, deadline, allow_empty=True)

    def _owned(self, resource, expected, allow_deleting=False):
        metadata = resource.get('metadata', {})
        if (metadata.get('deletionTimestamp') and not allow_deleting) or any(
                metadata.get('labels', {}).get(key) != value
                for key, value in expected['metadata']['labels'].items()):
            raise AdapterError('resource_conflict')
        for key, value in expected['metadata'].get('annotations', {}).items():
            if metadata.get('annotations', {}).get(key) != value:
                raise AdapterError('resource_conflict')

    def create(self, run_id, operation_id, model):
        """Höchstens ein Objekt erstellen; danach persistiert der Agent die Antwort."""
        desired = manifests(run_id, operation_id, model)
        deadline = time.monotonic() + self.timeout_seconds
        for control in infrastructure():
            namespace = control['metadata'].get('namespace')
            existing = self._object(control['kind'], control['metadata']['name'], deadline, namespace)
            if existing is None:
                self._request('create', ['-f', '-'], deadline, control)
                return {'complete': False, 'resources': []}
            self._owned(existing, control)
            if control['kind'] == 'ResourceQuota':
                if existing.get('spec', {}).get('hard') != control['spec']['hard']:
                    raise AdapterError('resource_conflict')
                observed = existing.get('status', {})
                if any(observed.get('hard', {}).get(key) != value or key not in observed.get('used', {})
                       for key, value in control['spec']['hard'].items()):
                    return {'complete': False, 'resources': []}
        resources = []
        for expected in desired:
            existing = self._object(expected['kind'], expected['metadata']['name'], deadline, NAMESPACE)
            if existing is None:
                if expected['kind'] == 'VirtualMachine':
                    machines = self._get(['virtualmachines', '-n', NAMESPACE], deadline)
                    if len(machines) >= MAX_VMS:
                        raise AdapterError('capacity_limit')
                existing = self._request('create', ['-f', '-'], deadline, expected)
                resources.append(reference(existing))
                return {'complete': expected['kind'] == 'Service', 'resources': resources}
            self._owned(existing, expected)
            resources.append(reference(existing))
        return {'complete': True, 'resources': resources}

    def status(self, run_id):
        name = resource_name(run_id)
        deadline = time.monotonic() + self.timeout_seconds
        # Ein noch nicht erstellter Namespace ist ein leerer laufbezogener Bestand.
        namespace = self._object('namespace', NAMESPACE, deadline)
        if namespace is None:
            items = []
        else:
            self._owned(namespace, infrastructure()[0], allow_deleting=True)
            items = self._get([
                'virtualmachines,virtualmachineinstances,datavolumes,persistentvolumeclaims,services,pods,endpointslices',
                '-n', NAMESPACE], deadline)
        owned = {}
        for item in items:
            metadata = item.get('metadata', {})
            if item['kind'] in ('VirtualMachine', 'Service') and metadata.get('name') == name:
                self._owned(item, {'metadata': {'labels': labels(run_id)}}, allow_deleting=True)
            if all(metadata.get('labels', {}).get(k) == v for k, v in labels(run_id).items()):
                owned[metadata['uid']] = item
        changed = True
        while changed:
            changed = False
            for item in items:
                metadata = item.get('metadata', {})
                if metadata['uid'] not in owned and any(
                        owner.get('uid') in owned for owner in metadata.get('ownerReferences', [])):
                    owned[metadata['uid']] = item
                    changed = True
        resources = [reference(item) for item in owned.values()]
        for item in list(owned.values()):
            volume = item.get('spec', {}).get('volumeName')
            if item['kind'] != 'PersistentVolumeClaim' or not volume:
                continue
            pv = self._object('persistentvolume', volume, deadline)
            if pv is None:
                continue
            claim = pv.get('spec', {}).get('claimRef', {})
            if not claim.get('uid') and item.get('status', {}).get('phase') != 'Bound':
                continue
            if (claim.get('uid'), claim.get('namespace'), claim.get('name')) != (
                    item['metadata']['uid'], NAMESPACE, item['metadata']['name']):
                raise AdapterError('resource_conflict')
            resources.append(reference(pv))
        vm = next((r for r in owned.values() if r['kind'] == 'VirtualMachine' and r['metadata']['name'] == name), {})
        vmi = next((r for r in owned.values() if r['kind'] == 'VirtualMachineInstance' and r['metadata']['name'] == name), {})
        service = next((r for r in owned.values() if r['kind'] == 'Service' and r['metadata']['name'] == name), {})
        result = {
            'resources': resources, 'vmState': vm.get('status', {}).get('printableStatus', 'Absent'),
            'vmiPhase': vmi.get('status', {}).get('phase', 'Absent'),
            'vmReady': vm.get('status', {}).get('ready') is True,
            'modelHash': vm.get('metadata', {}).get('annotations', {}).get('diplomarbeit/model-sha256'),
            'httpUrl': None, 'sshHost': None, 'sshPort': None,
        }
        node_name = vmi.get('status', {}).get('nodeName')
        if node_name and service:
            node = self._object('node', node_name, deadline)
            addresses = node.get('status', {}).get('addresses', []) if node else []
            address = next((a['address'] for a in addresses if a.get('type') == 'InternalIP'), None)
            if address:
                try:
                    address = str(ipaddress.ip_address(address))
                except ValueError as error:
                    raise AdapterError('invalid_response') from error
                host = '[' + address + ']' if ':' in address else address
                ports = {p['name']: p.get('nodePort') for p in service.get('spec', {}).get('ports', [])}
                if ports.get('http'):
                    result['httpUrl'] = f'http://{host}:{ports["http"]}/'
                result['sshHost'], result['sshPort'] = address, ports.get('ssh')
        return result

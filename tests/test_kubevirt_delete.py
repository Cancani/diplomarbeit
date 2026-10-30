from contextlib import closing, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapter.kubevirt_manifest import NAMESPACE, infrastructure, manifests, resource_name, labels
from adapter.kubevirt_lifecycle import KubeVirtLifecycle
from adapter.vertrag import AdapterError
from agent.lebenszyklus import delete
from agent.zustand import StateStore
from modell.validierung import load_model
from test_kubevirt_lifecycle import MemoryCluster


class DeletingCluster(MemoryCluster):
    def __init__(self):
        super().__init__()
        self.deletes = []

    def _request(self, verb, arguments, deadline, document=None, allow_empty=False, output_json=True):
        if verb != 'delete':
            return super()._request(verb, arguments, deadline, document, allow_empty)
        uid = document['preconditions']['uid']
        matches = [(key, value) for key, value in self.objects.items() if value['metadata']['uid'] == uid]
        if len(matches) != 1:
            raise AssertionError('Die UID-Bedingung muss genau ein bestehendes Objekt treffen.')
        key, item = matches[0]
        if not arguments[1].endswith('/' + item['metadata']['name']):
            raise AssertionError('API-Pfad und UID müssen dasselbe Objekt bezeichnen.')
        self.deletes.append(item['kind'])
        self.objects.pop(key)
        return {'kind': 'Status', 'status': 'Success'}


class KubeVirtDeleteTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.path = self.root/'state.sqlite3'
        self.data = self.root/'volume'
        self.data.mkdir()
        self.model = load_model(ROOT/'modell/beispiele/referenz.yaml')
        self.config = {'stateFile': self.path, 'adapters': {'kubevirt': {
            'command': 'unused', 'args': [], 'timeoutSeconds': 30}}}

    def cluster(self):
        cluster = DeletingCluster()
        for control in infrastructure():
            cluster.put(control)
        vm, service = manifests('run-01', 'create-operation', self.model)
        vm['metadata']['uid'] = 'vm-id'
        service['metadata']['uid'] = 'service-id'
        cluster.put(vm)
        cluster.put(service)
        name = resource_name('run-01')
        cluster.put({'kind': 'DataVolume', 'metadata': {
            'name': name + '-disk', 'namespace': NAMESPACE, 'uid': 'dv-id',
            'ownerReferences': [{'uid': 'vm-id'}]}})
        cluster.put({'kind': 'PersistentVolumeClaim', 'metadata': {
            'name': name + '-disk', 'namespace': NAMESPACE, 'uid': 'pvc-id',
            'ownerReferences': [{'uid': 'dv-id'}]},
            'spec': {'volumeName': 'pvc-pvc-id', 'storageClassName': 'microk8s-hostpath'},
            'status': {'phase': 'Bound'}})
        cluster.put({'kind': 'EndpointSlice', 'metadata': {
            'name': name + '-endpoint', 'namespace': NAMESPACE, 'uid': 'endpoint-id',
            'ownerReferences': [{'uid': 'service-id'}]}})
        cluster.put({'kind': 'PersistentVolume', 'metadata': {'name': 'pvc-pvc-id', 'uid': 'pv-id'},
            'spec': {'claimRef': {'name': name + '-disk', 'uid': 'pvc-id', 'namespace': NAMESPACE},
                     'storageClassName': 'microk8s-hostpath', 'persistentVolumeReclaimPolicy': 'Delete',
                     'hostPath': {'path': str(self.data)}, 'nodeAffinity': {'required': {'nodeSelectorTerms': [
                         {'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In',
                                                 'values': [socket.gethostname()]}]}]}}}})
        return cluster

    def test_delete_waits_for_pv_and_directory_and_keeps_control_infrastructure(self):
        cluster = self.cluster()
        known = {r['resource_id']: r for r in cluster.status('run-01')['resources']}
        for _ in range(10):
            step = cluster.delete('run-01', 'delete-operation', list(known.values()))
            for resource in step['resources']:
                known[resource['resource_id']] = resource
            for resource in step['removed']:
                known.pop(resource['resource_id'])
            if set(known) == {'pv-id'}:
                break
        self.assertEqual(set(known), {'pv-id'})
        self.assertNotIn('PersistentVolume', cluster.deletes)
        self.assertLess(cluster.deletes.index('VirtualMachine'), cluster.deletes.index('PersistentVolumeClaim'))
        self.assertFalse(cluster.delete('run-01', 'delete-operation', list(known.values()))['complete'])
        # Der Test übernimmt hier die Wirkung des Storage-Provisioners, nicht der Adapter.
        cluster.objects.pop(('persistentvolume', None, 'pvc-pvc-id'))
        self.assertFalse(cluster.delete('run-01', 'delete-operation', list(known.values()))['complete'])
        self.data.rmdir()
        step = cluster.delete('run-01', 'delete-operation', list(known.values()))
        self.assertTrue(step['complete'])
        self.assertEqual([r['resource_id'] for r in step['removed']], ['pv-id'])
        self.assertEqual({v['kind'] for v in cluster.objects.values()}, {'Namespace', 'ResourceQuota'})

    def test_new_storage_details_are_returned_before_any_mutation(self):
        cluster = self.cluster()
        resources = cluster.status('run-01')['resources']
        for resource in resources:
            resource.pop('details', None)
        step = cluster.delete('run-01', 'delete-operation', resources)
        self.assertFalse(step['complete'])
        self.assertEqual(cluster.deletes, [])
        pv = next(r for r in step['resources'] if r['kind'] == 'PersistentVolume')
        self.assertEqual(pv['details']['claimUid'], 'pvc-id')
        self.assertEqual(pv['details']['hostPath'], str(self.data))

    def test_foreign_scope_replacement_uid_and_retained_storage_block_deletion(self):
        cluster = self.cluster()
        resources = cluster.status('run-01')['resources']
        foreign = deepcopy(resources)
        foreign[0]['scope'] = 'default'
        with self.assertRaises(AdapterError):
            cluster.delete('run-01', 'delete-operation', foreign)
        old_status = cluster.status('run-01')
        cluster.objects[('virtualmachine', NAMESPACE, resource_name('run-01'))]['metadata']['uid'] = 'replacement'
        with patch.object(cluster, 'status', return_value=old_status), self.assertRaises(AdapterError) as caught:
            cluster.delete('run-01', 'delete-operation', resources)
        self.assertEqual(caught.exception.code, 'resource_conflict')
        self.assertEqual(cluster.deletes, [])
        cluster = self.cluster()
        cluster.objects[('persistentvolume', None, 'pvc-pvc-id')]['spec']['persistentVolumeReclaimPolicy'] = 'Retain'
        with self.assertRaises(AdapterError) as caught:
            cluster.delete('run-01', 'delete-operation', cluster.status('run-01')['resources'])
        self.assertEqual(caught.exception.code, 'storage_unverified')
        self.assertEqual(cluster.deletes, [])

    def test_raw_api_delete_has_uid_precondition_and_no_unsupported_output_flag(self):
        provider = KubeVirtLifecycle(['microk8s', 'kubectl'], 15)
        options = {'apiVersion': 'v1', 'kind': 'DeleteOptions',
                   'preconditions': {'uid': 'vm-id'}, 'propagationPolicy': 'Foreground'}
        with patch('adapter.kubevirt_provider.subprocess.run', return_value=subprocess.CompletedProcess(
                [], 0, '{"kind":"Status","status":"Success"}', '')) as run:
            provider._request('delete', ['--raw', '/apis/kubevirt.io/v1/namespaces/test/virtualmachines/vm', '-f', '-'],
                              time.monotonic() + 15, options, output_json=False)
        self.assertNotIn('-o', run.call_args.args[0])
        self.assertEqual(json.loads(run.call_args.kwargs['input']), options)

    def test_delete_race_confirms_absence_after_api_error(self):
        cluster = self.cluster()
        resources = cluster.status('run-01')['resources']
        request = cluster._request

        def disappearing(verb, *args, **kwargs):
            result = request(verb, *args, **kwargs)
            if verb == 'delete':
                raise AdapterError('platform_error')
            return result

        with patch.object(cluster, '_request', side_effect=disappearing):
            result = cluster.delete('run-01', 'delete-operation', resources)
        self.assertEqual([r['resource_id'] for r in result['removed']], ['vm-id'])
        self.assertFalse(result['complete'])

    def prepared_store(self):
        store = StateStore(self.path)
        store.start_create('run-01', 'create-operation', 'kubevirt', self.model)
        resources = self.cluster().status('run-01')['resources']
        store.observe_resources('run-01', 'create-operation', resources)
        store.advance('run-01', 'create-operation', 'ready')
        return store

    def test_agent_saves_storage_details_and_repeated_delete_only_checks_absence(self):
        store = self.prepared_store()
        store.start_operation('run-01', 'delete-operation', 'delete')
        store.fail('run-01', 'delete-operation', 'platform_error')
        state = {'deleted': False, 'delete_calls': 0}

        def call(adapter, tool, arguments, schema):
            record = store.get('run-01')
            if tool == 'status':
                return {'resources': [] if state['deleted'] else record['resources'],
                        'vmState': 'Absent', 'vmiPhase': 'Absent', 'vmReady': False, 'modelHash': None,
                        'httpUrl': None, 'sshHost': None, 'sshPort': None}
            self.assertEqual(tool, 'delete')
            self.assertEqual(next(r for r in record['resources'] if r['kind'] == 'PersistentVolume')['details']['claimUid'], 'pvc-id')
            state['deleted'] = True
            state['delete_calls'] += 1
            return {'complete': True, 'resources': [], 'removed': arguments['resources']}

        with patch('agent.lebenszyklus.call_tool', side_effect=call), redirect_stdout(io.StringIO()):
            delete(self.config, 'run-01', 'delete-operation')
            delete(self.config, 'run-01', 'delete-operation')
            delete(self.config, 'run-01', 'new-delete-operation')
        self.assertEqual(state['delete_calls'], 1)
        self.assertEqual(store.get('run-01')['phase'], 'absent')
        self.assertEqual(store.get('run-01')['resources'], [])

    def test_legacy_scratch_pv_metadata_is_recovered_before_any_deletion(self):
        cluster = self.cluster()
        name = resource_name('run-01')
        root = self.root/'provisioner'
        root.mkdir()
        main_path = root/f'{NAMESPACE}-{name}-disk-pvc-pvc-id'
        main_path.mkdir()
        cluster.objects[('persistentvolume', None, 'pvc-pvc-id')]['spec']['hostPath']['path'] = str(main_path)
        cluster.put({'kind': 'CDIConfig', 'metadata': {'name': 'config'},
                     'status': {'scratchSpaceStorageClass': 'microk8s-hostpath'}})
        resources = cluster.status('run-01')['resources']
        resources += [
            {'kind': 'PersistentVolumeClaim', 'name': name + '-disk-scratch',
             'resource_id': 'scratch-claim-id', 'scope': NAMESPACE},
            {'kind': 'PersistentVolume', 'name': 'pvc-scratch-claim-id',
             'resource_id': 'scratch-pv-id', 'scope': ''},
            {'kind': 'Pod', 'name': 'importer-' + name + '-disk',
             'resource_id': 'importer-old-1', 'scope': NAMESPACE},
            {'kind': 'Pod', 'name': 'importer-' + name + '-disk',
             'resource_id': 'importer-old-2', 'scope': NAMESPACE},
        ]
        step = cluster.delete('run-01', 'delete-operation', resources)
        self.assertEqual(cluster.deletes, [])
        self.assertFalse(step['complete'])
        recovered = next(r for r in step['resources'] if r['resource_id'] == 'scratch-pv-id')
        self.assertEqual(recovered['details'], {
            'claimUid': 'scratch-claim-id', 'claimName': name + '-disk-scratch',
            'hostPath': str(root/f'{NAMESPACE}-{name}-disk-scratch-pvc-scratch-claim-id'),
            'nodeName': socket.gethostname(),
            'pathSource': 'provisioner-name',
        })
        # Nach dem Speichern dürfen die bereits fehlenden Scratch-Objekte bestätigt werden.
        merged = {r['resource_id']: r for r in [*resources, *step['resources']]}
        self.assertIn('scratch-pv-id', merged)
        self.assertTrue(cluster._local_storage_gone(merged['scratch-pv-id']))
        for _ in range(10):
            result = cluster.delete('run-01', 'delete-operation', list(merged.values()))
            for resource in result['resources']:
                merged[resource['resource_id']] = resource
            for resource in result['removed']:
                merged.pop(resource['resource_id'])
            if all(r['kind'] == 'PersistentVolume' for r in merged.values()):
                break
        self.assertEqual(cluster.deletes[0], 'VirtualMachine')
        self.assertNotIn('PersistentVolume', cluster.deletes)
        self.assertNotIn('importer-old-1', merged)
        self.assertNotIn('importer-old-2', merged)
        cluster.objects.pop(('persistentvolume', None, 'pvc-pvc-id'))
        main_path.rmdir()
        self.assertTrue(cluster.delete('run-01', 'delete-operation', list(merged.values()))['complete'])

    def test_scratch_class_fallback_requires_the_known_target_claim(self):
        name = resource_name('run-01')
        root = self.root/'provisioner'
        root.mkdir()
        main_path = root/f'{NAMESPACE}-{name}-disk-pvc-pvc-id'
        main_path.mkdir()
        cases = [
            ({}, 'microk8s-hostpath', 'pvc-id', True),
            ({'status': {'scratchSpaceStorageClass': ''}}, 'microk8s-hostpath', 'pvc-id', True),
            ({'status': {'scratchSpaceStorageClass': 'other'}}, 'microk8s-hostpath', 'pvc-id', False),
            ({}, 'other', 'pvc-id', False),
            ({}, 'microk8s-hostpath', 'replacement-id', False),
            (None, 'microk8s-hostpath', 'pvc-id', False),
        ]
        for config, storage_class, uid, accepted in cases:
            with self.subTest(config=config, storage_class=storage_class, uid=uid):
                cluster = self.cluster()
                cluster.objects[('persistentvolume', None, 'pvc-pvc-id')]['spec']['hostPath']['path'] = str(main_path)
                resources = cluster.status('run-01')['resources'] + [
                    {'kind': 'PersistentVolumeClaim', 'name': name + '-disk-scratch',
                     'resource_id': 'scratch-claim-id', 'scope': NAMESPACE},
                    {'kind': 'PersistentVolume', 'name': 'pvc-scratch-claim-id',
                     'resource_id': 'scratch-pv-id', 'scope': ''},
                ]
                target = cluster.objects[('persistentvolumeclaim', NAMESPACE, name + '-disk')]
                target['spec']['storageClassName'] = storage_class
                target['metadata']['uid'] = uid
                if config is not None:
                    cluster.put({'kind': 'CDIConfig', 'metadata': {'name': 'config'}, **config})
                if accepted:
                    result = cluster.delete('run-01', 'delete-operation', resources)
                    recovered = next(r for r in result['resources'] if r['resource_id'] == 'scratch-pv-id')
                    self.assertEqual(recovered['details']['pathSource'], 'provisioner-name')
                    self.assertTrue(cluster._local_storage_gone(recovered))
                else:
                    with self.assertRaises(AdapterError):
                        cluster.delete('run-01', 'delete-operation', resources)
                self.assertEqual(cluster.deletes, [])

    def test_historical_pod_uid_does_not_delete_a_foreign_replacement(self):
        for own in [True, False]:
            with self.subTest(own=own):
                cluster = DeletingCluster()
                for control in infrastructure():
                    cluster.put(control)
                name = resource_name('run-01')
                pod = {'kind': 'Pod', 'metadata': {
                    'name': 'importer-' + name + '-disk', 'namespace': NAMESPACE, 'uid': 'pod-current',
                    'labels': labels('run-01') if own else {}}}
                cluster.put(pod)
                references = [
                    {'kind': 'VirtualMachine', 'name': name, 'scope': NAMESPACE, 'resource_id': 'vm-old'},
                    {'kind': 'Pod', 'name': pod['metadata']['name'], 'scope': NAMESPACE, 'resource_id': 'pod-old'},
                ]
                if own:
                    references.append({**references[1], 'resource_id': 'pod-current'})
                    result = cluster.delete('run-01', 'delete-operation', references)
                    self.assertEqual({r['resource_id'] for r in result['removed']}, {'vm-old', 'pod-old'})
                    self.assertEqual(cluster.deletes, ['Pod'])
                else:
                    with self.assertRaises(AdapterError) as caught:
                        cluster.delete('run-01', 'delete-operation', references)
                    self.assertEqual(caught.exception.code, 'resource_conflict')
                    self.assertEqual(cluster.deletes, [])

    def test_unknown_legacy_storage_is_not_discarded(self):
        cluster = DeletingCluster()
        for control in infrastructure():
            cluster.put(control)
        cluster.put({'kind': 'CDIConfig', 'metadata': {'name': 'config'},
                     'status': {'scratchSpaceStorageClass': 'microk8s-hostpath'}})
        resources = [
            {'kind': 'PersistentVolumeClaim', 'name': resource_name('run-01') + '-disk-scratch',
             'resource_id': 'scratch-claim-id', 'scope': NAMESPACE},
            {'kind': 'PersistentVolume', 'name': 'pvc-scratch-claim-id',
             'resource_id': 'scratch-pv-id', 'scope': ''},
        ]
        with self.assertRaises(AdapterError) as caught:
            cluster.delete('run-01', 'delete-operation', resources)
        self.assertEqual(caught.exception.code, 'storage_unverified')
        self.assertEqual(cluster.deletes, [])

    def test_timeout_preserves_known_storage_for_cleanup(self):
        store = self.prepared_store()

        def call(adapter, tool, arguments, schema):
            if tool == 'delete':
                raise AdapterError('timeout')
            return {'resources': store.get('run-01')['resources'], 'vmState': 'Running', 'vmiPhase': 'Running',
                    'vmReady': True, 'modelHash': store.get('run-01')['model_hash'],
                    'httpUrl': None, 'sshHost': None, 'sshPort': None}

        with patch('agent.lebenszyklus.call_tool', side_effect=call), redirect_stdout(io.StringIO()):
            with self.assertRaises(AdapterError):
                delete(self.config, 'run-01', 'delete-operation')
        record = store.get('run-01')
        self.assertEqual(record['phase'], 'error')
        self.assertEqual(record['operation']['error_code'], 'timeout')
        self.assertTrue(any(r['kind'] == 'PersistentVolume' and r.get('details') for r in record['resources']))

    def test_schema_two_migration_keeps_names_and_later_observations_keep_storage_details(self):
        store = self.prepared_store()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as connection:
            connection.execute('ALTER TABLE resources DROP COLUMN details')
            connection.execute('PRAGMA user_version = 2')
        store = StateStore(self.path)
        self.assertTrue(all(r['name'] for r in store.get('run-01')['resources']))
        resource = next(r for r in self.cluster().status('run-01')['resources'] if r['kind'] == 'PersistentVolume')
        store.observe_resources('run-01', 'create-operation', [resource])
        without_details = {k: v for k, v in resource.items() if k != 'details'}
        store.observe_resources('run-01', 'create-operation', [without_details])
        self.assertEqual(next(r for r in store.get('run-01')['resources'] if r['kind'] == 'PersistentVolume')['details'], resource['details'])


if __name__ == '__main__':
    unittest.main()

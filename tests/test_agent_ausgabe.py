from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.ausgabe import emit, output_mode, platform_result


class OutputTests(unittest.TestCase):
    def test_status_separates_stored_phase_vm_and_http_readiness_without_uid_dump(self):
        for phase, vm_ready, service_ready in [('error', True, True), ('ready', True, False)]:
            out = io.StringIO()
            with self.subTest(phase=phase), redirect_stdout(out), output_mode():
                emit('status', 'run-01', 'operation-01', storedPhase=phase,
                     vmState='Running', vmiPhase='Running', vmReady=vm_ready,
                     serviceReady=service_ready, httpUrl='http://test.invalid/',
                     sshHost='test.invalid', sshPort=2222,
                     resources=[{'kind': 'VirtualMachine', 'resource_id': 'internal-uid'}])
            text = out.getvalue()
            self.assertIn('Gespeicherter Zustand: ' + ('Fehler' if phase == 'error' else 'Bereit'), text)
            self.assertIn('HTTP-Dienst: ' + ('Bereit' if service_ready else 'Nicht bestätigt'), text)
            self.assertIn('Virtuelle Maschinen: 1', text)
            self.assertIn('Zugehörige Ressourcen: 0', text)
            self.assertNotIn('VM-Instanz:', text)
            self.assertIn('SSH: test.invalid, Port 2222', text)
            self.assertNotIn('internal-uid', text)

    def test_status_counts_machines_separately_from_related_resources(self):
        kubevirt = ['VirtualMachine', 'VirtualMachineInstance', 'Pod', 'DataVolume',
                    'PersistentVolumeClaim', 'PersistentVolume', 'Service', 'EndpointSlice']
        aws = ['EC2Instance', 'EBSVolume', 'NetworkInterface', 'SecurityGroup']
        for kinds, vmi_phase, expected in [
                (kubevirt, 'Scheduling', 'Zugehörige Ressourcen: 7 (Ausführung 2, Speicher 3, Netzwerk 2)'),
                (aws, 'Running', 'Zugehörige Ressourcen: 3 (Speicher 1, Netzwerk 2)'),
                (['VirtualMachine', 'Unbekannt'], 'Running', 'Zugehörige Ressourcen: 1 (Weitere 1)')]:
            out = io.StringIO()
            with self.subTest(kinds=kinds), redirect_stdout(out), output_mode():
                emit('status', 'run-01', 'operation-01', storedPhase='ready', vmState='Running',
                     vmiPhase=vmi_phase, vmReady=True, serviceReady=True, httpUrl=None,
                     sshHost=None, sshPort=None,
                     resources=[{'kind': kind, 'resource_id': 'uid'} for kind in kinds])
            text = out.getvalue()
            self.assertIn('Virtuelle Maschinen: 1', text)
            self.assertIn(expected, text)
            # Die VM-Instanz erscheint nur bei abweichendem Zustand.
            self.assertEqual('VM-Instanz: Wird eingeplant' in text, vmi_phase == 'Scheduling')

    def test_progress_does_not_claim_http_readiness_early_and_reduces_unchanged_delete_reports(self):
        out = io.StringIO()
        with redirect_stdout(out), output_mode(), patch('agent.ausgabe.time.monotonic', side_effect=[0, 5, 31, 32]):
            emit('reset_started', 'run-01', 'reset-01', stage='deleting')
            for count in (13, 13, 13, 4):
                emit('waiting_for_deletion', 'run-01', 'reset-01', knownResources=count)
            emit('reset_recreating', 'run-01', 'reset-01', modelHash='hash')
            emit('waiting', 'run-01', 'reset-01', vmReady=True, vmState='Running',
                 vmiPhase='Running', remainingSeconds=65)
        text = out.getvalue()
        self.assertEqual(text.count('Noch 13 bekannte Ressourcen'), 2)
        self.assertIn('Noch 4 bekannte Ressourcen', text)
        self.assertIn('HTTP-Dienst noch nicht bestätigt.', text)
        self.assertIn('Zeitlimit in 1 min 05 s.', text)
        self.assertNotIn('erfolgreich zurückgesetzt', text)

    def test_error_names_operation_id_for_resume(self):
        out = io.StringIO()
        with redirect_stdout(out), output_mode():
            emit('error', 'run-01', 'operation-01', code='interrupted', resources=[])
        self.assertIn('denselben Befehl mit --operation-id operation-01 ausführen.', out.getvalue())

    def test_json_retains_full_events_and_output_context_is_restored_after_exception(self):
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(RuntimeError), output_mode():
                raise RuntimeError('Ende des Ausgabe-Kontexts')
            with output_mode(json_output=True):
                emit('error', 'run-01', 'operation-01', code='timeout',
                     resources=[{'kind': 'VirtualMachine', 'resource_id': 'known-uid'}])
            emit('deleted', 'run-01', 'operation-01', alreadyAbsent=True)
        events = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(events[0]['resources'][0]['resource_id'], 'known-uid')
        self.assertEqual(events[0]['code'], 'timeout')
        self.assertIn('timeUtc', events[0])
        self.assertEqual(events[1]['event'], 'deleted')

    def test_platform_summary_distinguishes_unready_nodes_and_lists_machines(self):
        result = {'protocolVersion': 'test-version', 'status': {
            'platform': 'kubevirt', 'kubevirtPhase': 'Deployed',
            'nodes': [{'name': 'test-node', 'ready': False}],
            'virtualMachines': [{'namespace': 'test', 'name': 'vm', 'state': 'Stopped'}],
            'virtualMachineInstances': [],
        }}
        out = io.StringIO()
        with redirect_stdout(out):
            platform_result(result)
        text = out.getvalue()
        self.assertIn('test-node: Nicht bereit', text)
        self.assertIn('test/vm: Gestoppt', text)
        self.assertIn('VM-Instanzen: 0', text)
        out = io.StringIO()
        with redirect_stdout(out):
            platform_result(result, json_output=True)
        self.assertEqual(json.loads(out.getvalue()), result)


if __name__ == '__main__':
    unittest.main()

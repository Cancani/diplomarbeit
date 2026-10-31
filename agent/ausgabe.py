"""Lesbare CLI-Ausgabe und vollständige JSON-Ereignisse aus denselben Daten."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import time


_renderer = ContextVar('agent_output', default=None)
PHASES = {'absent': 'Nicht vorhanden', 'creating': 'Wird erstellt', 'ready': 'Bereit',
          'deleting': 'Wird gelöscht', 'error': 'Fehler'}
VM_STATES = {'Absent': 'Nicht vorhanden', 'Provisioning': 'Wird bereitgestellt',
             'Pending': 'Wartet', 'Scheduling': 'Wird eingeplant', 'Scheduled': 'Eingeplant',
             'Starting': 'Wird gestartet', 'Running': 'Läuft', 'Terminating': 'Wird entfernt',
             'Stopped': 'Gestoppt', 'Stopping': 'Wird gestoppt', 'Failed': 'Fehler',
             'Succeeded': 'Beendet', 'Unknown': 'Unbekannt'}


def machine_state(value):
    return VM_STATES.get(value, f'Unbekannt ({json.dumps(value, ensure_ascii=False)})')


def emit(event, run_id, operation_id, **values):
    data = {'timeUtc': datetime.now(timezone.utc).isoformat(), 'event': event,
            'runId': run_id, 'operationId': operation_id, **values}
    renderer = _renderer.get()
    if renderer is None:
        print(json.dumps(data, ensure_ascii=False), flush=True)
    else:
        renderer(data)


@contextmanager
def output_mode(json_output=False):
    # Direkte Python-Aufrufe behalten JSON. Nur die CLI wählt die Textansicht.
    token = _renderer.set(None if json_output else HumanOutput())
    try:
        yield
    finally:
        _renderer.reset(token)


def write(message=''):
    print(message, flush=True)


class HumanOutput:
    def __init__(self):
        self.run = None
        self.operation = None
        self.action = None
        self.last_delete_count = None
        self.last_delete_report = float('-inf')

    def context(self, data):
        if self.run != data['runId']:
            write(f'Lauf: {data["runId"]}')
            self.run = data['runId']
        if self.operation != data['operationId']:
            write(f'Auftrag: {data["operationId"]}')
            self.operation = data['operationId']

    def access(self, data):
        if data.get('httpUrl'):
            write(f'HTTP: {data["httpUrl"]}')
        if data.get('sshHost') and data.get('sshPort'):
            write(f'SSH: {data["sshHost"]}, Port {data["sshPort"]}')

    def __call__(self, data):
        self.context(data)
        event = data['event']
        if event in ('create_started', 'reset_started', 'delete_started'):
            self.action = event
            message = {'create_started': 'Lernumgebung wird erstellt.',
                       'delete_started': 'Lernumgebung wird vollständig entfernt.',
                       'reset_started': 'Lernumgebung wird zurückgesetzt.'}[event]
            write(message)
            if event == 'reset_started':
                write('Bestehende Ressourcen entfernen.' if data['stage'] == 'deleting'
                      else 'Neuerstellung aus dem gespeicherten Modell fortsetzen.')
        elif event == 'operation_recovered':
            write('Unterbrochener Auftrag nach Plattformabgleich übernommen.')
            write(f'Fortsetzung: {PHASES.get(data["stage"], "Unbekannt")}')
        elif event == 'resources_recorded':
            labels = {'VirtualMachine': 'VM', 'Service': 'Netzwerkdienst'}
            kinds = ', '.join(dict.fromkeys(labels.get(r['kind'], r['kind']) for r in data['resources']))
            write(f'Ressourcen bestätigt: {kinds}.')
        elif event == 'waiting_for_readiness':
            write('VM- und HTTP-Bereitschaft werden geprüft.')
        elif event == 'waiting':
            if data['vmReady'] and data['vmiPhase'] == 'Running':
                message = 'VM läuft. HTTP-Dienst noch nicht bestätigt.'
            else:
                state = machine_state(data['vmState'])
                message = f'VM: {state}. Bereitschaft noch nicht bestätigt.'
            minutes, seconds = divmod(data['remainingSeconds'], 60)
            write(f'{message} Zeitlimit in {minutes} min {seconds:02} s.')
        elif event == 'waiting_for_deletion':
            count, now = data['knownResources'], time.monotonic()
            if count != self.last_delete_count or now - self.last_delete_report >= 30:
                write(f'Abbau läuft. Noch {count} bekannte Ressourcen zu prüfen.')
                self.last_delete_count, self.last_delete_report = count, now
        elif event == 'removal_confirmed':
            write(f'Entfernung bestätigt: {len(data["resources"])} Ressourcen.')
        elif event == 'reset_recreating':
            write('Abbau vollständig bestätigt. Umgebung wird aus dem gespeicherten Modell neu erstellt.')
        elif event == 'ready':
            write('VM und HTTP-Dienst sind bereit.' if self.action == 'reset_started'
                  else 'Lernumgebung erfolgreich erstellt. VM und HTTP-Dienst sind bereit.')
            self.access(data)
        elif event == 'reset_completed':
            write('Lernumgebung erfolgreich zurückgesetzt.')
        elif event == 'deleted':
            write('Lernumgebung ist bereits vollständig entfernt.' if data['alreadyAbsent']
                  else 'Lernumgebung vollständig entfernt.')
        elif event == 'status':
            write(f'Gespeicherter Zustand: {PHASES.get(data["storedPhase"], "Unbekannt")}')
            write(f'VM: {machine_state(data["vmState"])}')
            write(f'VM-Instanz: {machine_state(data["vmiPhase"])}')
            write(f'VM-Bereitschaft: {"Ja" if data["vmReady"] else "Nein"}')
            write(f'HTTP-Dienst: {"Bereit" if data["serviceReady"] else "Nicht bestätigt"}')
            write(f'Aktuell beobachtete Ressourcen: {len(data["resources"])}')
            self.access(data)
        elif event == 'error':
            write('Gespeicherter Zustand: Fehler')
            write(f'Bekannte Ressourcen zur weiteren Prüfung: {len(data["resources"])}')
            write('Bestand mit status prüfen. Zum Fortsetzen denselben Befehl und dieselbe Operationskennung verwenden.')


def platform_result(result, json_output=False):
    if json_output:
        write(json.dumps(result, ensure_ascii=False, indent=2))
        return
    status = result['status']
    write(f'Plattform: {status["platform"]}')
    write('MCP-Verbindung: Erreichbar')
    write(f'KubeVirt: {"Betriebsbereit" if status["kubevirtPhase"] == "Deployed" else status["kubevirtPhase"]}')
    write(f'Knoten: {len(status["nodes"])}')
    for node in status['nodes']:
        write(f'  {node["name"]}: {"Bereit" if node["ready"] else "Nicht bereit"}')
    for field, label in [('virtualMachines', 'VMs'), ('virtualMachineInstances', 'VM-Instanzen')]:
        write(f'{label}: {len(status[field])}')
        for machine in status[field]:
            write(f'  {machine["namespace"]}/{machine["name"]}: {machine_state(machine["state"])}')

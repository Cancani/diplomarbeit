"""Lesbare CLI-Ausgabe und vollständige JSON-Ereignisse aus denselben Daten."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
from threading import Lock
import time


_renderer = ContextVar('agent_output', default=None)
_prefix = ContextVar('agent_output_prefix', default=None)
_output_lock = Lock()
PLATFORMS = {'kubevirt': 'KubeVirt', 'aws': 'AWS EC2'}
PHASES = {'absent': 'Nicht vorhanden', 'creating': 'Wird erstellt', 'ready': 'Bereit',
          'deleting': 'Wird gelöscht', 'error': 'Fehler'}
VM_STATES = {'Absent': 'Nicht vorhanden', 'Provisioning': 'Wird bereitgestellt',
             'Pending': 'Wartet', 'Scheduling': 'Wird eingeplant', 'Scheduled': 'Eingeplant',
             'Starting': 'Wird gestartet', 'Running': 'Läuft', 'Terminating': 'Wird entfernt',
             'Stopped': 'Gestoppt', 'Stopping': 'Wird gestoppt', 'Failed': 'Fehler',
             'Succeeded': 'Beendet', 'Unknown': 'Unbekannt'}
VM_KINDS = ('VirtualMachine', 'EC2Instance')
RESOURCE_GROUPS = {'VirtualMachineInstance': 'Ausführung', 'Pod': 'Ausführung',
                   'DataVolume': 'Speicher', 'PersistentVolumeClaim': 'Speicher',
                   'PersistentVolume': 'Speicher', 'EBSVolume': 'Speicher',
                   'Service': 'Netzwerk', 'EndpointSlice': 'Netzwerk',
                   'NetworkInterface': 'Netzwerk', 'SecurityGroup': 'Netzwerk'}


def machine_state(value):
    return VM_STATES.get(value, f'Unbekannt ({json.dumps(value, ensure_ascii=False)})')


def resource_summary(resources):
    """VMs getrennt von den zugehörigen Ressourcen zählen."""
    machines = sum(1 for resource in resources if resource['kind'] in VM_KINDS)
    counts = {}
    for resource in resources:
        if resource['kind'] not in VM_KINDS:
            group = RESOURCE_GROUPS.get(resource['kind'], 'Weitere')
            counts[group] = counts.get(group, 0) + 1
    details = ', '.join(f'{group} {counts[group]}'
                        for group in ('Ausführung', 'Speicher', 'Netzwerk', 'Weitere') if group in counts)
    related = sum(counts.values())
    return machines, f'{related} ({details})' if details else '0'


def emit(event, run_id, operation_id, **values):
    data = {'timeUtc': datetime.now(timezone.utc).isoformat(), 'event': event,
            'runId': run_id, 'operationId': operation_id, **values}
    renderer = _renderer.get()
    with _output_lock:
        if renderer is None:
            print(json.dumps(data, ensure_ascii=False), flush=True)
        else:
            renderer(data)


@contextmanager
def output_mode(json_output=False, *, prefix=None):
    # Direkte Python-Aufrufe behalten JSON. Nur die CLI wählt die Textansicht.
    token = _renderer.set(None if json_output else HumanOutput())
    prefix_token = _prefix.set(prefix)
    try:
        yield
    finally:
        _renderer.reset(token)
        _prefix.reset(prefix_token)


def write(message=''):
    if prefix := _prefix.get():
        message = f'[{prefix}] {message}'
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
            # Die VM-Instanz nur zeigen, wenn sie etwas anderes meldet als die VM.
            if machine_state(data['vmiPhase']) != machine_state(data['vmState']):
                write(f'VM-Instanz: {machine_state(data["vmiPhase"])}')
            write(f'VM-Bereitschaft: {"Ja" if data["vmReady"] else "Nein"}')
            write(f'HTTP-Dienst: {"Bereit" if data["serviceReady"] else "Nicht bestätigt"}')
            machines, related = resource_summary(data['resources'])
            write(f'Virtuelle Maschinen: {machines}')
            write(f'Zugehörige Ressourcen: {related}')
            self.access(data)
        elif event == 'error':
            write('Gespeicherter Zustand: Fehler')
            write(f'Bekannte Ressourcen zur weiteren Prüfung: {len(data["resources"])}')
            write('Bestand mit status prüfen. Zum Fortsetzen denselben Befehl mit '
                  f'--operation-id {data["operationId"]} ausführen.')


def run_overview(runs, json_output=False):
    """Gespeicherte Läufe auflisten; die Angaben stammen nur aus SQLite."""
    if json_output:
        data = {'timeUtc': datetime.now(timezone.utc).isoformat(), 'event': 'overview', 'runs': [
            {'runId': run['run_id'], 'platform': run['platform'], 'storedPhase': run['phase'],
             'updatedAt': run['updated_at']} for run in runs]}
        write(json.dumps(data, ensure_ascii=False))
        return
    if not runs:
        write('Es sind keine Lernumgebungen gespeichert.')
        return
    rows = [('Laufkennung', 'Plattform', 'Gespeicherter Zustand', 'Letzte Änderung (UTC)')]
    for run in runs:
        rows.append((run['run_id'], PLATFORMS.get(run['platform'], run['platform']),
                     PHASES.get(run['phase'], 'Unbekannt'), run['updated_at'][:16].replace('T', ' ')))
    widths = [max(len(row[column]) for row in rows) for column in range(4)]
    write(f'Gespeicherte Lernumgebungen: {len(runs)}')
    for row in rows:
        write('  '.join(value.ljust(width) for value, width in zip(row, widths)).rstrip())
    write('Live-Zustand einer Lernumgebung: status --run-id <Laufkennung>')


def platform_result(result, json_output=False):
    if json_output:
        write(json.dumps(result, ensure_ascii=False, indent=2))
        return
    status = result['status']
    write(f'Plattform: {status["platform"]}')
    write('MCP-Verbindung: Erreichbar')
    if status['platform'] == 'aws':
        write(f'AWS-Region: {status["region"]}')
        write(f'Vom Agenten gekennzeichnete EC2-Instanzen: {len(status["instances"])}')
        for instance in status['instances']:
            write(f'  {instance["id"]}: {instance["state"]}')
        return
    write(f'KubeVirt: {"Betriebsbereit" if status["kubevirtPhase"] == "Deployed" else status["kubevirtPhase"]}')
    write(f'Knoten: {len(status["nodes"])}')
    for node in status['nodes']:
        write(f'  {node["name"]}: {"Bereit" if node["ready"] else "Nicht bereit"}')
    for field, label in [('virtualMachines', 'VMs'), ('virtualMachineInstances', 'VM-Instanzen')]:
        write(f'{label}: {len(status[field])}')
        for machine in status[field]:
            write(f'  {machine["namespace"]}/{machine["name"]}: {machine_state(machine["state"])}')

#!/usr/bin/env python3
"""LernMAAS-Messung vorbereiten und lesend beobachten; keine Bereitstellung."""
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def query(*args):
    result = subprocess.run(['maas', 'ubuntu', *args], check=True,
                            capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def machine_summary(machine):
    """Nur benötigte Felder; Zonenbeschreibungen enthalten VPN-Schlüssel."""
    result = {k: machine.get(k) for k in (
        'system_id', 'hostname', 'status_name', 'ip_addresses',
        'cpu_count', 'memory', 'osystem', 'distro_series', 'architecture', 'hwe_kernel')}
    for field in ('zone', 'pool', 'pod'):
        value = machine.get(field) or {}
        result[field] = {key: value.get(key) for key in ('id', 'name')}
    return result


def save_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def prepare(root, number):
    run_id = f'maas-{number}-20260930'
    suffix = f'da20260930{number}'
    target = f'daref-01-{suffix}'
    pool = f'daref-{suffix}'
    folder = root / run_id
    if folder.exists():
        raise ValueError(f'Laufordner existiert bereits: {folder}. Nicht überschreiben.')
    for manifest in ('SHA256SUMS', 'SHA256SUMS-vorbereitung', 'probe-http.sha256'):
        for line in (root / manifest).read_text().splitlines():
            digest, filename = line.split(None, 1)
            path = root / filename.lstrip('*')
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Prüfsumme stimmt nicht: {filename}')
    key = Path.home() / '.ssh/diplomarbeit-lernmaas-20260930'
    public = subprocess.run(['ssh-keygen', '-y', '-f', str(key)],
                            check=True, capture_output=True, text=True).stdout.split()[:2]
    prepared = (root / 'zugang.pub').read_text().split()[:2]
    cloud = (root / 'cloud-init-referenz.yaml').read_text()
    if public != prepared or ' '.join(public) not in cloud:
        raise ValueError('Schlüssel und vorbereitete Cloud-init-Datei stimmen nicht überein.')
    ntp = subprocess.run(['timedatectl', 'show', '-p', 'NTPSynchronized'],
                         check=True, capture_output=True, text=True).stdout.strip()
    if ntp != 'NTPSynchronized=yes':
        raise ValueError('Zeitsynchronisation ist nicht bestätigt.')
    machines = query('machines', 'read')
    pools = query('resource-pools', 'read')
    if any(m.get('hostname') == target for m in machines):
        raise ValueError('Zielhostname ist bereits vorhanden.')
    if any(p.get('name') == pool for p in pools):
        raise ValueError('Zielpool ist bereits vorhanden.')
    # Vorherige formale Testressourcen müssen vollständig abgebaut sein.
    if any(re.fullmatch(r'daref-da20260930b[0-9]{2}', p.get('name', '')) for p in pools):
        raise ValueError('Ein Testpool der Messserie existiert noch. Erst Abbau prüfen.')
    hosts = query('pods', 'read')
    if not hosts or hosts[0].get('id') != 7:
        raise ValueError('createvms würde nicht mehr zuerst Pod 7 verwenden.')
    image = query('boot-resource', 'read', '11')
    original_image = json.loads((root / 'ubuntu-noble-ga24.04.json').read_text())
    for field in ('name', 'architecture', 'sets'):
        if image.get(field) != original_image.get(field):
            raise ValueError('Der MAAS-Abbildstand hat sich seit der Vorbereitung geändert.')
    folder.mkdir()
    for filename in ('createvms-original.sh', 'config-referenz.yaml',
                     'cloud-init-referenz.yaml', 'zugang.pub', 'probe-http.py'):
        shutil.copyfile(root / filename, folder / filename)
    shutil.copyfile(Path(__file__), folder / 'maas-beobachten.py')
    (folder / 'zeitsynchronisation.txt').write_text(ntp + '\n')
    (folder / 'bedienung.csv').write_text(
        'phase;abschnitt;aktive_sekunden;anzahl_handlungen;bemerkung\n'
        'Aufbau;createvms ausführen und Ausgabe prüfen;;;\n'
        'Aufbau;Zone setzen;;;\n'
        'Aufbau;Deployment konfigurieren und bestätigen;;;\n'
        'Prüfung;SSH und Konfiguration prüfen;;;\n'
        'Abbau;Löschblock ausführen und Ergebnis prüfen;;;\n'
        'Messführung;Beobachter bedienen und Messnotizen schreiben;;;\n', encoding='utf-8')
    save_json(folder / 'plan.json', {
        'run_id': run_id, 'hostname': target, 'pool_name': pool,
        'suffix': suffix, 'pod_id': 7, 'prepared_utc': now(),
        'observer_timeout_s': 1800, 'http_timeout_s': 900,
        'observer_interval_s': 2, 'guest_port': 8080,
        'active_time_method': 'Externe Stoppuhr; Abschnitte nach Anleitung getrennt erfassen',
        'private_key_path': str(key),
    })
    save_json(folder / 'maschinen-vorher.json', [machine_summary(m) for m in machines])
    save_json(folder / 'pools-vorher.json', [{k: p.get(k) for k in ('id', 'name')} for p in pools])
    save_json(folder / 'hosts-vorher.json', [{k: h.get(k) for k in (
        'id', 'name', 'total', 'used', 'available',
        'cpu_over_commit_ratio', 'memory_over_commit_ratio')} for h in hosts])
    save_json(folder / 'abbild-vorher.json', image)
    input_names = ('createvms-original.sh', 'config-referenz.yaml',
                   'cloud-init-referenz.yaml', 'zugang.pub', 'probe-http.py', 'maas-beobachten.py')
    (folder / 'SHA256SUMS-eingaben').write_text(''.join(
        f'{hashlib.sha256((folder / n).read_bytes()).hexdigest()}  {n}\n' for n in input_names))
    print(f'Vorbereitung abgeschlossen: {folder}', flush=True)
    print(f'Ziel: {target}; Pool: {pool}. Noch keine Messung gestartet.', flush=True)
    return folder


def observe(folder):
    plan = json.loads((folder / 'plan.json').read_text())
    if (folder / 'start-utc.txt').exists() or (folder / 'statusbeobachtung.jsonl').exists():
        raise ValueError('Messung wurde bereits begonnen. Nicht erneut starten.')
    for line in (folder / 'SHA256SUMS-eingaben').read_text().splitlines():
        digest, name = line.split(None, 1)
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Eingabe verändert: {name}')
    if any(m.get('hostname') == plan['hostname'] for m in query('machines', 'read')):
        raise ValueError('Zielmaschine existiert bereits vor dem Messstart.')
    if any(p.get('name') == plan['pool_name'] for p in query('resource-pools', 'read')):
        raise ValueError('Zielpool existiert bereits vor dem Messstart.')
    print('Anleitung vollständig bereitlegen; zweites Terminal für createvms öffnen.')
    input('Stoppuhr bereit? Mit Enter beginnt die Aufbau-Messung: ')
    (folder / 'start-utc.txt').write_text(now() + '\n')
    deadline = time.monotonic() + plan['observer_timeout_s']
    with (folder / 'statusbeobachtung.jsonl').open('x', encoding='utf-8') as stream:
        def record(**data):
            stream.write(json.dumps({'time_utc': now(), **data}) + '\n')
            stream.flush()
        record(event='observer_start', run_id=plan['run_id'])
        print('Messung läuft. Jetzt createvms im zweiten Terminal ausführen.', flush=True)
        last_status = None
        while time.monotonic() < deadline:
            cycle_start = time.monotonic()
            matches = [m for m in query('machines', 'read')
                       if m.get('hostname') == plan['hostname']]
            if len(matches) > 1:
                raise ValueError('Mehrere Maschinen mit dem Zielnamen gefunden.')
            if matches:
                m = machine_summary(matches[0])
                if m['pool'].get('name') != plan['pool_name']:
                    raise ValueError('Zielmaschine hat eine unerwartete Poolzuordnung.')
                record(event='machine', **m)
                if m['status_name'] != last_status:
                    print(f'{now()}: {m["status_name"]}', flush=True)
                    last_status = m['status_name']
                ips = [ip for ip in (m['ip_addresses'] or []) if
                       ipaddress.ip_address(ip) in ipaddress.ip_network('10.0.45.0/24')]
                if m['status_name'] in ('Deploying', 'Deployed') and len(ips) == 1:
                    save_json(folder / 'zielmaschine.json', m)
                    (folder / 'system-id.txt').write_text(m['system_id'] + '\n')
                    (folder / 'vm-ip.txt').write_text(ips[0] + '\n')
                    url = f'http://{ips[0]}:8080/'
                    record(event='http_observer_start', url=url)
                    print(f'HTTP-Beobachtung: {url}', flush=True)
                    timeout = min(plan['http_timeout_s'], deadline-time.monotonic())
                    if timeout <= 0:
                        raise TimeoutError('Gesamtzeitgrenze erreicht.')
                    result = subprocess.run([
                        sys.executable, str(folder / 'probe-http.py'), url,
                        '--run-id', plan['run_id'], '--output', str(folder / 'http-create.jsonl'),
                        '--timeout', str(timeout), '--interval', '2'], timeout=timeout+10)
                    record(event='http_observer_end', exitcode=result.returncode)
                    if result.returncode != 0:
                        raise ValueError('HTTP-Zeitgrenze erreicht oder Prüfung fehlgeschlagen.')
                    machine = query('machine', 'read', m['system_id'])
                    save_json(folder / 'maschine-nach-http.json', machine_summary(machine))
                    print('HTTP erfolgreich. Weiter mit SSH-Prüfung gemäss Anleitung.', flush=True)
                    return
            time.sleep(max(0, 2-(time.monotonic()-cycle_start)))
        record(event='timeout')
        raise TimeoutError('Innerhalb von 1800 Sekunden kein nutzbarer Endpunkt gefunden.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'observe', 'mark-delete'))
    parser.add_argument('number', help='Neue Laufnummer b01 bis b99')
    parser.add_argument('--root', type=Path, default=Path.home() / 'diplomarbeit-laeufe/lernmaas-basis-20260930')
    args = parser.parse_args()
    if not re.fullmatch(r'b(?:0[1-9]|[1-9][0-9])', args.number):
        parser.error('Laufnummer muss zwischen b01 und b99 liegen.')
    try:
        if args.action == 'prepare':
            prepare(args.root, args.number)
        elif args.action == 'observe':
            observe(args.root / f'maas-{args.number}-20260930')
        else:
            folder = args.root / f'maas-{args.number}-20260930'
            if not (folder / 'system-id.txt').is_file():
                raise ValueError('Kein erfasstes Maschinenziel für diesen Lauf.')
            if (folder / 'abbau-start-utc.txt').exists():
                raise ValueError('Abbau wurde bereits begonnen.')
            input('Abbaublock bereit und Stoppuhr bereit? Enter startet die Abbau-Messung: ')
            with (folder / 'abbau-start-utc.txt').open('x') as stream:
                stream.write(now() + '\n')
            print('Abbau-Messung läuft. Jetzt den vorbereiteten Abbaublock ausführen.')
    except (ValueError, OSError, subprocess.SubprocessError, TimeoutError, KeyboardInterrupt) as error:
        print(f'Abgebrochen: {type(error).__name__}: {error}', file=sys.stderr)
        print('Keine automatische Löschung. Vorhandene Testressourcen gezielt prüfen.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

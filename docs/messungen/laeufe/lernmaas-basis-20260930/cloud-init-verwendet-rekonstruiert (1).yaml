import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import ipaddress

folder = Path(__file__).resolve().parent
target = "daref-01-da20260930a"
deadline = time.monotonic() + 1800

with (folder / "statusbeobachtung.jsonl").open("x") as log:
    def record(**data):
        row = {
            "time_utc": datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            **data,
        }
        log.write(json.dumps(row) + "\n")
        log.flush()

    record(event="observer_start", hostname=target)
    print("Beobachtung bereit. Warte auf " + target, flush=True)

    while time.monotonic() < deadline:
        try:
            result = subprocess.run(
                ["maas", "ubuntu", "machines", "read"],
                capture_output=True, text=True,
                check=True, timeout=15,
            )
            machines = json.loads(result.stdout)
        except (subprocess.SubprocessError, ValueError) as error:
            record(event="query_error", error=type(error).__name__)
            time.sleep(2)
            continue

        matches = [m for m in machines if m.get("hostname") == target]
        if len(matches) > 1:
            record(event="error", reason="Hostname nicht eindeutig")
            sys.exit("Abbruch: Mehrere Maschinen mit dem Zielnamen.")

        if matches:
            machine = matches[0]
            addresses = machine.get("ip_addresses") or []
            record(
                event="machine",
                system_id=machine["system_id"],
                status=machine.get("status_name"),
                addresses=addresses,
            )

            if machine.get("status_name") == "Deployed":
                ips = [
                    ip for ip in addresses
                    if ipaddress.ip_address(ip) in
                    ipaddress.ip_network("10.0.45.0/24")
                ]
                if len(ips) == 1:
                    url = f"http://{ips[0]}:8080/"
                    record(event="http_observer_start", url=url)
                    (folder / "system-id.txt").write_text(
                        machine["system_id"] + "\n"
                    )
                    (folder / "vm-ip.txt").write_text(ips[0] + "\n")
                    print("HTTP-Prüfung: " + url, flush=True)
                    check = subprocess.run([
                        sys.executable, str(folder.parent / "probe-http.py"),
                        url,
                        "--run-id", "lernmaas-20260930-01",
                        "--output", str(folder / "http-create.jsonl"),
                        "--timeout", "900",
                        "--interval", "2",
                    ])
                    record(event="http_observer_end", exitcode=check.returncode)
                    print("HTTP-Prüfung beendet, Exitcode:", check.returncode)
                    sys.exit(check.returncode)

        time.sleep(2)

    record(event="timeout")
    sys.exit("Abbruch: Innerhalb von 30 Minuten keine passende bereitgestellte VM.")

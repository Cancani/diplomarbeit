#!/usr/bin/env python3
"""Read-only HTTP observer. Its duration is not the provisioning duration."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def observe(url, run_id, output, expected='lernumgebung bereit', timeout=900, interval=2, request_timeout=2):
    if any(not math.isfinite(x) or x <= 0 for x in (timeout, interval, request_timeout)):
        raise ValueError('Zeitwerte müssen positiv und endlich sein')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('HTTP(S)-Endpunkt ohne Zugangsdaten erforderlich')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    opener = build_opener(NoRedirect())
    # Exclusive mode protects evidence from an accidental second run.
    with Path(output).open('x', encoding='utf-8') as log:
        start = time.monotonic()
        def record(**values):
            row = dict(time_utc=utc_now(), observer_elapsed_s=round(time.monotonic()-start, 3), run_id=run_id, **values)
            log.write(json.dumps(row, ensure_ascii=False)+'\n'); log.flush()
        record(event='observer_start', url=url, expected=expected, interval_s=interval, timeout_s=timeout, request_timeout_s=request_timeout)
        attempt = 0
        while time.monotonic()-start < timeout:
            began = time.monotonic(); attempt += 1
            ready = False
            result = {}
            try:
                remaining = timeout-(began-start)
                with opener.open(Request(url, headers={'Cache-Control':'no-cache'}), timeout=min(request_timeout, remaining)) as response:
                    # Reference payload is tiny. Cap reads and reject oversized bodies.
                    payload = response.read(4097)
                    text = payload.decode('utf-8', errors='replace')
                    content_ok = len(payload) <= 4096 and text.rstrip('\r\n') == expected
                    result = dict(status=response.status, content_matches=content_ok, bytes_read=len(payload))
                    ready = response.status == 200 and content_ok
            except HTTPError as error:
                result = dict(status=error.code, error='HTTPError')
            except (URLError, TimeoutError, OSError) as error:
                result = dict(error=type(error).__name__)
            in_time = time.monotonic()-start <= timeout
            record(event='probe', attempt=attempt, ready=ready and in_time, **result)
            if ready and in_time:
                record(event='ready_observed')
                return 0
            # Polling is scheduled start-to-start; slower requests cause later observations.
            pause = min(max(0, interval-(time.monotonic()-began)), max(0, timeout-(time.monotonic()-start)))
            if pause: time.sleep(pause)
        record(event='timeout')
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected', default='lernumgebung bereit')
    parser.add_argument('--timeout', type=float, default=900)
    parser.add_argument('--interval', type=float, default=2)
    parser.add_argument('--request-timeout', type=float, default=2)
    args = parser.parse_args()
    try:
        return observe(args.url, args.run_id, args.output, args.expected, args.timeout, args.interval, args.request_timeout)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())

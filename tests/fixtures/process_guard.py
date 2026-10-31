"""Eigenständiger Testprozess für Sperren ohne Aufräumen durch den Agenten."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gemeinsam.prozessschutz import adapter_guard, run_guard


mode, ready = sys.argv[1], Path(sys.argv[2])
guard = run_guard(Path(sys.argv[3]), 'test-run') if mode == 'agent' else adapter_guard()
with guard as session:
    ready.write_text(json.dumps(session), encoding='utf-8')
    sys.stdin.read()

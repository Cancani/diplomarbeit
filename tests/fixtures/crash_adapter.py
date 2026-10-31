"""Persistente Testplattform: Änderung vor einer noch ausstehenden MCP-Antwort."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from adapter.kubevirt import create_server
from agent.zustand import StateStore
from gemeinsam.prozessschutz import adapter_guard
from modell.snapshot import encode_snapshot


actual, state, url = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
resource = {'kind': 'VirtualMachine', 'name': 'test-vm', 'resource_id': 'unchanged-uid', 'scope': 'test'}


class Platform:
    def create(self, run_id, operation_id, model):
        if actual.exists():
            # Nach dem Verlust der ersten Antwort muss vor dieser Änderung
            # bereits das unabhängig gespeicherte Plattforminventar bekannt sein.
            assert resource in StateStore(state).get(run_id)['resources']
        else:
            _, model_hash = encode_snapshot(model)
            actual.write_text(json.dumps({'modelHash': model_hash}), encoding='utf-8')
            actual.with_suffix('.ready').touch()
            deadline = time.monotonic() + 15
            while not actual.with_suffix('.release').exists():
                if time.monotonic() > deadline:
                    raise RuntimeError('Der Test hat den Adapter nicht freigegeben.')
                time.sleep(0.02)
        return {'complete': True, 'resources': [resource]}

    def status(self, run_id):
        return {'resources': [resource], 'vmReady': True, 'vmState': 'Running',
                'vmiPhase': 'Running', 'modelHash': json.loads(actual.read_text(encoding='utf-8'))['modelHash'],
                'httpUrl': url, 'sshHost': None, 'sshPort': None}


with adapter_guard():
    create_server(Platform()).run(transport='stdio')

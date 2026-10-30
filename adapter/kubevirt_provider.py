"""Lesende kubectl-Aufrufe, unabhängig vom MCP-Transport."""
import json
import subprocess
import time

from adapter.vertrag import AdapterError


class KubeVirtProvider:
    def __init__(self, command, timeout_seconds):
        self.command = list(command)
        self.timeout_seconds = timeout_seconds

    def _get(self, arguments, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('timeout')
        try:
            result = subprocess.run(
                [*self.command, 'get', *arguments, '-o', 'json',
                 f'--request-timeout={max(1, int(remaining))}s'],
                capture_output=True, text=True, encoding='utf-8',
                timeout=remaining, check=False)
        except subprocess.TimeoutExpired as error:
            raise AdapterError('timeout') from error
        except FileNotFoundError as error:
            raise AdapterError('command_not_found') from error
        except UnicodeError as error:
            raise AdapterError('invalid_response') from error
        except OSError as error:
            raise AdapterError('platform_error') from error
        if result.returncode != 0:
            raise AdapterError('platform_error')
        try:
            document = json.loads(result.stdout)
            if not isinstance(document, dict) or not isinstance(document.get('items'), list):
                raise ValueError('Eine Kubernetes-Liste wird erwartet.')
            return document['items']
        except (ValueError, UnicodeError) as error:
            raise AdapterError('invalid_response') from error

    def platform_status(self):
        deadline = time.monotonic() + self.timeout_seconds
        nodes = self._get(['nodes'], deadline)
        installations = self._get(['kubevirt', '-n', 'kubevirt'], deadline)
        machines = self._get(['virtualmachines,virtualmachineinstances', '-A'], deadline)
        try:
            result = {
                'platform': 'kubevirt',
                'nodes': [{
                    'name': node['metadata']['name'],
                    'ready': any(condition.get('type') == 'Ready' and condition.get('status') == 'True'
                                 for condition in node.get('status', {}).get('conditions', [])),
                } for node in nodes],
                'kubevirtPhase': installations[0].get('status', {}).get('phase', 'Unknown')
                                 if len(installations) == 1 else 'Unknown',
                'virtualMachines': [], 'virtualMachineInstances': [],
            }
            for machine in machines:
                kind = machine['kind']
                if kind not in ('VirtualMachine', 'VirtualMachineInstance'):
                    raise AdapterError('invalid_response')
                metadata = machine['metadata']
                field = 'virtualMachines' if kind == 'VirtualMachine' else 'virtualMachineInstances'
                state_field = 'printableStatus' if kind == 'VirtualMachine' else 'phase'
                result[field].append({
                    'name': metadata['name'], 'namespace': metadata['namespace'], 'id': metadata['uid'],
                    'state': machine.get('status', {}).get(state_field, 'Unknown'),
                })
            return result
        except (KeyError, TypeError, AttributeError) as error:
            raise AdapterError('invalid_response') from error

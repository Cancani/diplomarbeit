"""Lebenszyklus steuern, Inventar sichern und Endzustände prüfen."""
from datetime import datetime, timezone
from functools import wraps
import asyncio
import json
import time

import anyio
import httpx2

from adapter.kubevirt_manifest import validate_id
from adapter.vertrag import AdapterError, CREATE_SCHEMA, RUN_STATUS_SCHEMA, DELETE_SCHEMA
from agent.mcp_client import call_tool
from agent.zustand import StateError, StateStore
from modell.snapshot import encode_snapshot
from gemeinsam.prozessschutz import ProcessGuardError, run_guard


def emit(event, run_id, operation_id, **values):
    print(json.dumps({'timeUtc': datetime.now(timezone.utc).isoformat(), 'event': event,
                      'runId': run_id, 'operationId': operation_id, **values}, ensure_ascii=False), flush=True)


async def _service_ready(url, model, timeout):
    if not url:
        return False
    expected = model['vm']['testService']
    try:
        with anyio.fail_after(timeout):
            async with httpx2.AsyncClient(trust_env=False, follow_redirects=False, timeout=timeout) as client:
                async with client.stream('GET', url, headers={'Cache-Control': 'no-cache',
                                                              'Accept-Encoding': 'identity'}) as response:
                    if response.status_code != expected['expectedStatus']:
                        return False
                    payload = b''
                    async for chunk in response.aiter_bytes(chunk_size=4097):
                        payload += chunk
                        if len(payload) > 4096:
                            return False
                    return payload.decode('utf-8').rstrip('\r\n') == expected['expectedBody']
    except (httpx2.HTTPError, OSError, UnicodeError, TimeoutError):
        return False


def service_ready(url, model, timeout=2):
    return asyncio.run(_service_ready(url, model, timeout))


def _adapter(config, platform):
    if platform != 'kubevirt' or platform not in config['adapters']:
        raise StateError('Für diese Plattform ist die Lebenszyklussteuerung noch nicht verfügbar.')
    return {**config['adapters'][platform], '_processGuard': config.get('_processGuard', {})}


def _guarded(action):
    @wraps(action)
    def execute(config, run_id, *arguments, **options):
        validate_id(run_id)
        if action.__name__ != 'create' and not config['stateFile'].is_file():
            raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
        try:
            with run_guard(config['stateFile'], run_id) as session:
                return action({**config, '_processGuard': session}, run_id, *arguments, **options)
        except ProcessGuardError as error:
            raise StateError(str(error)) from error
    return execute


def _recover(store, adapter, record):
    if record['operation']['status'] != 'running':
        return record
    if not record['operation']['guarded']:
        raise StateError('Dieser laufende Altauftrag hat keinen Prozessschutz; eine automatische Wiederaufnahme ist nicht zulässig.')
    # Die erworbene Sitzung schliesst aktive bisherige Agenten/Adapter aus.
    # Vor weiteren Änderungen zuerst auch verlorene API-Antworten abgleichen.
    _read(store, adapter, record)
    operation_id = record['operation']['operation_id']
    store.fail(record['run_id'], operation_id, 'interrupted')
    emit('operation_recovered', record['run_id'], operation_id, stage=record['operation']['stage'])
    return store.get(record['run_id'])


def _read(store, adapter, record, timeout=None):
    settings = dict(adapter)
    if timeout is not None:
        if timeout <= 0:
            raise AdapterError('timeout')
        settings['timeoutSeconds'] = min(settings['timeoutSeconds'], timeout)
    actual = call_tool(settings, 'status', {'run_id': record['run_id']}, RUN_STATUS_SCHEMA)
    if actual['modelHash'] is not None and actual['modelHash'] != record['model_hash']:
        raise AdapterError('resource_conflict')
    store.observe_resources(record['run_id'], record['operation']['operation_id'], actual['resources'])
    return actual


def status(config, run_id):
    validate_id(run_id)
    if not config['stateFile'].is_file():
        raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
    store = StateStore(config['stateFile'])
    record = store.get(run_id)
    actual = _read(store, _adapter(config, record['platform']), record)
    ready = (actual['vmReady'] and actual['vmiPhase'] == 'Running'
             and service_ready(actual['httpUrl'], record['model_snapshot']))
    emit('status', run_id, record['operation']['operation_id'], storedPhase=record['phase'],
         serviceReady=ready, **actual)
    return actual, ready


def _failed(store, adapter, record, error):
    # Auch eine verlorene API-Antwort kann Ressourcen hinterlassen haben.
    try:
        _read(store, adapter, record)
    except (AdapterError, StateError):
        pass
    code = 'interrupted' if isinstance(error, KeyboardInterrupt) else (
        'timeout' if error.code == 'timeout' else 'platform_error')
    run_id, operation_id = record['run_id'], record['operation']['operation_id']
    store.fail(run_id, operation_id, code)
    emit('error', run_id, operation_id, code=code, resources=store.get(run_id)['resources'])


@_guarded
def create(config, run_id, operation_id, platform, model, timeout_seconds=900):
    validate_id(run_id)
    validate_id(operation_id)
    snapshot, _ = encode_snapshot(model)
    adapter = _adapter(config, platform)
    store = StateStore(config['stateFile'])
    try:
        previous = store.get(run_id)
    except StateError:
        previous = None
    if previous:
        old_snapshot, _ = encode_snapshot(previous['model_snapshot'])
        if old_snapshot != snapshot or previous['platform'] != platform:
            raise StateError('Plattform und Modell-Snapshot eines Laufs dürfen nicht verändert werden.')
        previous = _recover(store, adapter, previous)
    if previous and previous['phase'] == 'ready':
        result = status(config, run_id)
        if not result[1]:
            raise AdapterError('platform_error')
        return result
    store.start_create(run_id, operation_id, platform, model, guarded=True)
    emit('create_started', run_id, operation_id)
    record = store.get(run_id)
    try:
        return _create(store, adapter, record, time.monotonic() + timeout_seconds)
    except (AdapterError, KeyboardInterrupt) as error:
        _failed(store, adapter, record, error)
        raise


def _stored_run(config, run_id):
    if not config['stateFile'].is_file():
        raise StateError('Für diese Laufkennung ist keine Umgebung gespeichert.')
    store = StateStore(config['stateFile'])
    record = store.get(run_id)
    return store, record, _adapter(config, record['platform'])


@_guarded
def delete(config, run_id, operation_id, timeout_seconds=300):
    validate_id(run_id)
    validate_id(operation_id)
    store, record, adapter = _stored_run(config, run_id)
    record = _recover(store, adapter, record)
    if record['phase'] == 'absent':
        actual = call_tool(adapter, 'status', {'run_id': run_id}, RUN_STATUS_SCHEMA)
        if actual['resources']:
            raise AdapterError('resource_conflict')
        if record['operation']['operation_id'] != operation_id:
            store.start_operation(run_id, operation_id, 'delete', guarded=True)
        emit('deleted', run_id, operation_id, alreadyAbsent=True)
        return
    store.start_operation(run_id, operation_id, 'delete', guarded=True)
    record = store.get(run_id)
    emit('delete_started', run_id, operation_id)
    try:
        _delete(store, adapter, record, time.monotonic() + timeout_seconds)
        store.advance(run_id, operation_id, 'absent')
        emit('deleted', run_id, operation_id, alreadyAbsent=False)
    except (AdapterError, KeyboardInterrupt) as error:
        _failed(store, adapter, record, error)
        raise


@_guarded
def reset(config, run_id, operation_id, timeout_seconds=1200):
    validate_id(run_id)
    validate_id(operation_id)
    store, record, adapter = _stored_run(config, run_id)
    record = _recover(store, adapter, record)
    previous = record['operation']
    if (previous['operation_id'] == operation_id and previous['kind'] == 'reset'
            and previous['status'] == 'succeeded' and record['phase'] == 'ready'):
        result = status(config, run_id)
        if not result[1]:
            raise AdapterError('platform_error')
        return result
    store.start_operation(run_id, operation_id, 'reset', guarded=True)
    record = store.get(run_id)
    deadline = time.monotonic() + timeout_seconds
    emit('reset_started', run_id, operation_id, stage=record['phase'])
    try:
        if record['phase'] == 'deleting':
            _delete(store, adapter, record, deadline)
            store.advance(run_id, operation_id, 'creating')
            emit('reset_recreating', run_id, operation_id, modelHash=record['model_hash'])
        result = _create(store, adapter, record, deadline)
        emit('reset_completed', run_id, operation_id, modelHash=record['model_hash'])
        return result
    except (AdapterError, KeyboardInterrupt) as error:
        _failed(store, adapter, record, error)
        raise


def _create(store, adapter, record, deadline):
    run_id, operation_id = record['run_id'], record['operation']['operation_id']
    model = record['model_snapshot']
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('timeout')
        settings = {**adapter, 'timeoutSeconds': min(adapter['timeoutSeconds'], remaining)}
        step = call_tool(settings, 'create', {
            'run_id': run_id, 'operation_id': operation_id, 'model': model}, CREATE_SCHEMA)
        store.observe_resources(run_id, operation_id, step['resources'])
        if step['resources']:
            emit('resources_recorded', run_id, operation_id, resources=step['resources'])
        if step['complete']:
            break
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    emit('waiting_for_readiness', run_id, operation_id)
    last_state = None
    last_report = time.monotonic()
    while True:
        actual = _read(store, adapter, record, deadline - time.monotonic())
        remaining = deadline - time.monotonic()
        ready = (remaining > 0 and actual['vmReady'] and actual['vmiPhase'] == 'Running'
                 and service_ready(actual['httpUrl'], model, min(2, remaining)))
        if ready and time.monotonic() <= deadline:
            store.advance(run_id, operation_id, 'ready')
            emit('ready', run_id, operation_id, serviceReady=True, **actual)
            return actual, True
        current_state = (actual['vmState'], actual['vmiPhase'], actual['vmReady'])
        if current_state != last_state or time.monotonic() - last_report >= 30:
            emit('waiting', run_id, operation_id, vmState=actual['vmState'], vmiPhase=actual['vmiPhase'],
                 vmReady=actual['vmReady'], remainingSeconds=max(0, int(deadline - time.monotonic())))
            last_state, last_report = current_state, time.monotonic()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('timeout')
        time.sleep(min(2, remaining))


def _delete(store, adapter, record, deadline):
    run_id, operation_id = record['run_id'], record['operation']['operation_id']
    while True:
        remaining = deadline - time.monotonic()
        _read(store, adapter, record, remaining)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('timeout')
        known = store.get(run_id)['resources']
        settings = {**adapter, 'timeoutSeconds': min(adapter['timeoutSeconds'], remaining)}
        step = call_tool(settings, 'delete', {
            'run_id': run_id, 'operation_id': operation_id, 'resources': known}, DELETE_SCHEMA)
        store.observe_resources(run_id, operation_id, step['resources'])
        for resource in step['removed']:
            store.confirm_removed(run_id, operation_id, resource['kind'],
                                  resource['resource_id'], resource['scope'])
        if step['removed']:
            emit('removal_confirmed', run_id, operation_id, resources=step['removed'])
        if step['complete']:
            final = _read(store, adapter, record, deadline - time.monotonic())
            if not final['resources'] and not store.get(run_id)['resources']:
                return
        emit('waiting_for_deletion', run_id, operation_id,
             knownResources=len(store.get(run_id)['resources']))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError('timeout')
        time.sleep(min(2, remaining))

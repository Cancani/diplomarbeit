"""Konfigurierten MCP-Prozess starten und eine lesende Abfrage ausführen."""
import asyncio
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters

from adapter.vertrag import AdapterError, read_status_response, read_result


ROOT = Path(__file__).resolve().parents[1]


def _leaves(error):
    if isinstance(error, BaseExceptionGroup):
        return [leaf for child in error.exceptions for leaf in _leaves(child)]
    return [error]


async def _call(adapter_config, tool, arguments, reader):
    parameters = StdioServerParameters(
        command=adapter_config['command'], args=adapter_config['args'], cwd=ROOT,
        env={'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
    timeout = adapter_config['timeoutSeconds']
    try:
        with anyio.fail_after(timeout):
            async with Client(parameters, read_timeout_seconds=timeout) as client:
                result = await client.call_tool(tool, arguments)
                if result.is_error:
                    raise AdapterError('platform_error')
                data = reader(result.structured_content)
                return {'protocolVersion': client.protocol_version, 'data': data}
    except Exception as error:
        leaves = _leaves(error)
        for leaf in leaves:
            if isinstance(leaf, AdapterError):
                raise leaf from error
        if any(isinstance(leaf, TimeoutError) for leaf in leaves):
            raise AdapterError('timeout') from error
        raise AdapterError('transport_error') from error


def platform_status(adapter_config):
    result = asyncio.run(_call(adapter_config, 'platform_status', {}, read_status_response))
    return {'protocolVersion': result['protocolVersion'], 'status': result['data']}


def call_tool(adapter_config, tool, arguments, schema):
    return asyncio.run(_call(adapter_config, tool, arguments, lambda response: read_result(response, schema)))['data']

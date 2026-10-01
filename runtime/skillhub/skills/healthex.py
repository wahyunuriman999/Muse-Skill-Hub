"""HealthEx driver — passthrough to HealthEx's official MCP server.

HealthEx exposes its clinical tools (get_medications, get_labs, get_vitals, ...)
over MCP at https://api.healthex.io/mcp. This driver opens a real MCP session
with your token and proxies tool calls.

Setup: get a HealthEx auth token from your HealthEx account and set
HEALTHEX_AUTH_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import _proxy

SKILL = "healthex"
REQUIRED_ENV = ["HEALTHEX_AUTH_TOKEN"]
SETUP_HELP = (
    "Get an auth token from your HealthEx account (https://healthex.io) "
    "and set HEALTHEX_AUTH_TOKEN."
)

_MCP_URL = "https://api.healthex.io/mcp"


def _token() -> str:
    token = os.environ.get("HEALTHEX_AUTH_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def _session():
    from mcp.client.streamable_http import streamablehttp_client
    from mcp import ClientSession
    import httpx

    headers = {"Authorization": f"Bearer {_token()}"}
    client = streamablehttp_client(_MCP_URL, headers=headers)
    read, write, _ = await client.__aenter__()
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    return client, session


async def _close(client, session):
    try:
        await session.__aexit__(None, None, None)
    finally:
        await client.__aexit__(None, None, None)


async def list_tools(params: dict) -> dict:
    client, session = await _session()
    try:
        tools = await session.list_tools()
        return {"status": "ok", "tools": [
            {"name": t.name, "description": t.description} for t in tools.tools]}
    finally:
        await _close(client, session)


async def call_tool(params: dict) -> dict:
    client, session = await _session()
    try:
        result = await session.call_tool(params["tool"],
                                         arguments=params.get("arguments", {}))
        parts = []
        for c in result.content:
            if hasattr(c, "text"):
                parts.append(c.text)
            else:
                parts.append(str(c))
        return {"status": "ok", "tool": params["tool"],
                "is_error": result.isError, "content": parts}
    finally:
        await _close(client, session)


ACTIONS = {
    "list_tools": ActionDef("List the clinical tools HealthEx exposes.",
        {}, [], list_tools),
    "call_tool": ActionDef("Call a HealthEx tool (e.g. get_medications, get_labs).",
        {"tool": {"type": "string"},
         "arguments": {"type": "object", "default": {}}},
        ["tool"], call_tool),
}

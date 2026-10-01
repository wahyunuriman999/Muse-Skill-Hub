"""Muse Skill Hub MCP server (v2) — every action is its own typed MCP tool.

Tool names look like ``github_search_repositories`` with full JSON schemas
inlined (no opaque ``params`` object). Plus ``skillhub_search_capabilities``
for dynamic capability discovery.

Run:
    python -m skillhub.server        # stdio transport (Claude Desktop, etc.)
    skillhub-server                  # after pip install
"""
from __future__ import annotations

import asyncio
import json
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from . import __version__
from .errors import DriverNotImplemented, SkillError
from .registry import (dispatch, load_registry, mcp_tools, search_capabilities,
                       split_tool_name)

server = Server("muse-skill-hub")
REGISTRY = load_registry()
TOOLS = mcp_tools(REGISTRY)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name=t["name"], description=t["description"],
                 inputSchema=t["inputSchema"]) for t in TOOLS]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    arguments = arguments or {}
    if name == "skillhub_search_capabilities":
        results = search_capabilities(
            REGISTRY, arguments.get("query", ""),
            top_k=int(arguments.get("top_k", 8)))
        return [TextContent(type="text",
                            text=json.dumps({"status": "ok", "matches": results},
                                            indent=2))]

    split = split_tool_name(REGISTRY, name)
    if split is None:
        payload = {"ok": False,
                   "error": {"code": "not_found",
                             "message": f"Unknown tool '{name}'.",
                             "retryable": False},
                   "meta": {"request_id": "", "skill": "", "action": ""}}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    skill, action = split
    entry = REGISTRY[skill]
    # control args are popped; everything else is action params
    confirm = bool(arguments.pop("confirm", False))
    approval_id = arguments.pop("approval_id", None)
    idempotency_key = arguments.pop("idempotency_key", None)

    try:
        if not entry.implemented:
            raise DriverNotImplemented(skill)
        result = await dispatch(entry, action, arguments, confirm=confirm,
                                approval_id=approval_id,
                                idempotency_key=idempotency_key)
    except SkillError as exc:
        result = exc.to_dict()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    n_impl = sum(1 for e in REGISTRY.values() if e.implemented)
    print(f"muse-skill-hub v{__version__}: {len(REGISTRY)} skills registered, "
          f"{n_impl} with executable drivers, {len(TOOLS)} MCP tools.",
          file=sys.stderr)
    asyncio.run(_run())


if __name__ == "__main__":
    main()

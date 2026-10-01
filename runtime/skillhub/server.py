"""Muse Skill Hub MCP server — exposes all 87 skills as executable MCP tools.

Run:
    python -m skillhub.server        # stdio transport (Claude Desktop, etc.)
    skillhub-server                  # after pip install

Claude Desktop config (~/.config/Claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "muse-skill-hub": {
          "command": "/path/to/venv/bin/python",
          "args": ["-m", "skillhub.server"],
          "env": { "GITHUB_TOKEN": "...", "SLACK_BOT_TOKEN": "..." }
        }
      }
    }
"""
from __future__ import annotations

import asyncio
import json
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .errors import DriverNotImplemented, SkillError
from .registry import dispatch, load_registry, tool_schema

server = Server("muse-skill-hub")
REGISTRY = load_registry()


@server.list_tools()
async def list_tools() -> list[Tool]:
    tools = []
    for name, entry in REGISTRY.items():
        suffix = "" if entry.implemented else " (catalog only — driver not implemented yet)"
        tools.append(
            Tool(
                name=name,
                description=entry.description + suffix,
                inputSchema=tool_schema(entry),
            )
        )
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    entry = REGISTRY.get(name)
    if entry is None:
        payload = {"status": "error", "code": "unknown_skill",
                   "message": f"Unknown skill '{name}'."}
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    action = (arguments or {}).get("action", "info")
    params = (arguments or {}).get("params", {}) or {}
    confirm = bool((arguments or {}).get("confirm", False))

    try:
        if not entry.implemented:
            raise DriverNotImplemented(name)
        result = await dispatch(entry, action, params, confirm)
    except SkillError as exc:
        result = exc.to_dict()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    n_impl = sum(1 for e in REGISTRY.values() if e.implemented)
    print(f"muse-skill-hub: {len(REGISTRY)} skills registered, "
          f"{n_impl} with executable drivers.", file=sys.stderr)
    asyncio.run(_run())


if __name__ == "__main__":
    main()

"""Smoke tests proving the runtime actually executes.

Run:  pytest tests/ -v
"""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from skillhub import registry
from skillhub.errors import ConfirmationRequired, CredentialsMissing, DriverNotImplemented


def test_registry_loads_all_skills():
    reg = registry.load_registry()
    assert len(reg) == 97, f"expected 97 skills, got {len(reg)}"
    implemented = [n for n, e in reg.items() if e.implemented]
    assert len(implemented) >= 10, f"expected >=10 drivers, got {len(implemented)}"
    print(f"\n  97 skills loaded, {len(implemented)} with executable drivers: "
          f"{sorted(implemented)}")


def test_every_skill_has_valid_tool_schema():
    reg = registry.load_registry()
    for name, entry in reg.items():
        schema = registry.tool_schema(entry)
        assert schema["type"] == "object"
        assert "action" in schema["properties"]
        assert "action" in schema["required"]


@pytest.mark.asyncio
async def test_github_search_executes_real_api_call():
    """Proof of real execution: hits api.github.com live, no token needed."""
    reg = registry.load_registry()
    result = await registry.dispatch(
        reg["github"], "search_repositories",
        {"query": "model context protocol", "per_page": 3}, confirm=False)
    assert result["status"] == "ok"
    assert result["total_count"] > 0
    assert len(result["repositories"]) > 0
    assert "full_name" in result["repositories"][0]
    print(f"\n  live GitHub search returned: "
          f"{result['repositories'][0]['full_name']}")


@pytest.mark.asyncio
async def test_missing_credentials_return_structured_error():
    """Drivers without credentials fail honestly — never fake success."""
    reg = registry.load_registry()
    env = {k: v for k, v in os.environ.items() if k != "SLACK_BOT_TOKEN"}
    old = os.environ.get("SLACK_BOT_TOKEN")
    os.environ.pop("SLACK_BOT_TOKEN", None)
    try:
        with pytest.raises(CredentialsMissing) as exc:
            await registry.dispatch(reg["slack"], "list_channels", {}, confirm=False)
        assert "SLACK_BOT_TOKEN" in exc.value.to_dict()["missing_env"]
        print(f"\n  honest error: {exc.value.to_dict()['code']}")
    finally:
        if old is not None:
            os.environ["SLACK_BOT_TOKEN"] = old


@pytest.mark.asyncio
async def test_write_action_requires_confirmation():
    """Read/write isolation is enforced in code, not just docs."""
    reg = registry.load_registry()
    with pytest.raises(ConfirmationRequired) as exc:
        await registry.dispatch(
            reg["github"], "create_issue",
            {"owner": "x", "repo": "y", "title": "t"}, confirm=False)
    assert exc.value.to_dict()["code"] == "confirmation_required"


@pytest.mark.asyncio
async def test_unimplemented_skill_is_honest():
    reg = registry.load_registry()
    not_impl = [n for n, e in reg.items() if not e.implemented]
    assert not_impl, "expected some catalog-only skills"
    with pytest.raises(DriverNotImplemented):
        await registry.dispatch(reg[not_impl[0]], "info", {}, confirm=False)


@pytest.mark.asyncio
async def test_mcp_server_end_to_end_over_stdio():
    """Full proof: boot the real MCP server, list 87 tools, call one live."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_script = str(
        __import__("pathlib").Path(__file__).resolve().parent.parent / "skillhub" / "server.py")
    params = StdioServerParameters(
        command=sys.executable, args=["-c",
            f"import sys; sys.path.insert(0, {str(__import__('pathlib').Path(server_script).parent.parent)!r});"
            " from skillhub.server import main; main()"],
        env={**os.environ, "PYTHONPATH": str(
            __import__("pathlib").Path(__file__).resolve().parent.parent)},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 97, f"got {len(tools.tools)} tools"
            names = {t.name for t in tools.tools}
            assert "github" in names and "slack" in names

            res = await session.call_tool(
                "github", {"action": "search_repositories",
                           "params": {"query": "mcp", "per_page": 2}})
            payload = json.loads(res.content[0].text)
            assert payload["status"] == "ok"
            assert payload["total_count"] > 0

            res2 = await session.call_tool("replit", {"action": "info", "params": {}})
            payload2 = json.loads(res2.content[0].text)
            assert payload2["code"] == "driver_not_implemented"
    print("\n  MCP server served 97 tools over stdio; live call succeeded")

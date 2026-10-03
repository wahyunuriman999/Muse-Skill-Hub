"""GATE 10 — MCP documentation consistency.

The MCP surface is one tool per action with flat, inlined parameters —
no opaque ``{action, params}`` envelope. Proven here:
  1. tool count matches the published catalog number (210);
  2. every tool name is unique (no skill/action collision);
  3. split_tool_name round-trips every tool back to its (skill, action);
  4. each inputSchema carries the driver's params, the driver's required
     list, additionalProperties=False, and the control args
     (confirm/approval_id/idempotency_key) exactly for non-read risks;
  5. every tool description states its risk tier;
  6. no stale ``{action, params, confirm}`` envelope docs remain.
"""
from __future__ import annotations

from pathlib import Path

from skillhub.policy import risk_for
from skillhub.registry import (
    action_tool_name,
    load_registry,
    mcp_tools,
    split_tool_name,
)

REG = load_registry()
ALL_TOOLS = mcp_tools(REG)
TOOLS = [t for t in ALL_TOOLS if t["name"] != "skillhub_search_capabilities"]


def test_tool_count_matches_catalog():
    # 221 action tools + skillhub_search_capabilities = 222 published
    assert len(ALL_TOOLS) == 222
    assert len(TOOLS) == 221
    assert any(t["name"] == "skillhub_search_capabilities" for t in ALL_TOOLS)


def test_tool_names_unique():
    names = [t["name"] for t in TOOLS]
    assert len(set(names)) == len(names)


def test_tool_names_round_trip():
    for tool in TOOLS:
        split = split_tool_name(REG, tool["name"])
        assert split is not None, f"unresolvable tool name: {tool['name']}"
        skill, action = split
        assert action_tool_name(skill, action) == tool["name"]


def test_schemas_match_drivers():
    for tool in TOOLS:
        skill, action = split_tool_name(REG, tool["name"])
        ad = REG[skill].actions[action]
        risk = risk_for(skill, action, ad.risk)
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"] == list(ad.required or [])
        for param in (ad.parameters or {}):
            assert param in schema["properties"], \
                f"{tool['name']}: driver param '{param}' missing from MCP schema"
        if risk == "read":
            for ctrl in ("confirm", "approval_id", "idempotency_key"):
                assert ctrl not in schema["properties"], \
                    f"{tool['name']}: read tool must not take '{ctrl}'"
        else:
            for ctrl in ("confirm", "approval_id", "idempotency_key"):
                assert ctrl in schema["properties"], \
                    f"{tool['name']}: non-read tool missing '{ctrl}'"


def test_descriptions_state_risk():
    for tool in TOOLS:
        skill, action = split_tool_name(REG, tool["name"])
        risk = risk_for(skill, action, REG[skill].actions[action].risk)
        assert f"Risk: {risk}." in tool["description"], \
            f"{tool['name']}: description does not state risk"


def test_no_stale_envelope_docs():
    root = Path(__file__).resolve().parent.parent.parent
    hits = []
    for readme in (root / "README.md", root / "runtime" / "README.md"):
        text = readme.read_text(encoding="utf-8")
        if "Every tool takes `{ action, params, confirm }`" in text:
            hits.append(str(readme))
    assert hits == [], f"stale envelope docs in: {hits}"

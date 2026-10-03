"""Tests for tools/live_contracts.py — the live contract-test runner.

No network is used here: specs are inspected, the read-only guard is
proven, and SKIP paths are exercised. Live execution itself is proven
by real runs recorded in visibility/live-contracts-report.md.
"""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import live_contracts as lc


def test_curated_specs_present():
    specs = lc.build_specs()
    by_skill = {s["skill"]: s for s in specs}
    for skill in ("podcast", "github", "stripe", "lovable", "replit",
                  "granola", "ticketmaster", "flightaware"):
        assert skill in by_skill, f"missing curated spec: {skill}"
    assert by_skill["podcast"]["tier"] == "public"
    assert by_skill["github"]["env"] == ["GITHUB_TOKEN"]


def test_all_specs_are_read_only():
    from skillhub import registry
    reg = registry.load_registry()
    for spec in lc.build_specs():
        if not spec["action"]:
            continue
        action_def = reg[spec["skill"]].actions[spec["action"]]
        assert action_def.risk == "read", \
            f"{spec['skill']}.{spec['action']} is not read-only"


def test_missing_key_skips(monkeypatch):
    async def go():
        from skillhub import registry
        reg = registry.load_registry()
        spec = {"skill": "stripe", "action": "list_customers",
                "params": {"limit": 1}, "env": ["STRIPE_SECRET_KEY"],
                "tier": "keyed", "expect": "customers"}
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        return await lc._run_one(reg, spec)

    out = asyncio.run(go())
    assert out["status"] == "SKIP"
    assert "STRIPE_SECRET_KEY" in out["reason"]


def test_non_read_action_refused():
    async def go():
        from skillhub import registry
        reg = registry.load_registry()
        spec = {"skill": "stripe", "action": "create_customer",
                "params": {}, "env": [], "tier": "keyed", "expect": None}
        return await lc._run_one(reg, spec)

    out = asyncio.run(go())
    assert out["status"] == "SKIP"
    assert "not a read action" in out["reason"]


def test_markdown_report_renders():
    md = lc._markdown([
        {"skill": "podcast", "action": "search_podcasts", "tier": "public",
         "status": "PASS", "duration_ms": 600},
        {"skill": "stripe", "status": "SKIP",
         "reason": "needs STRIPE_SECRET_KEY"},
    ])
    assert "| podcast |" in md
    assert "STRIPE_SECRET_KEY" in md
    assert "1 PASS" in md

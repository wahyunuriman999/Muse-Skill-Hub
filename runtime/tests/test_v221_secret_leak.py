"""GATE 16 — exception & secret leak assurance.

A secret canary is pushed through EVERY surface that renders errors or
data; the canary must appear NOWHERE except the in-memory objects the
caller already holds:

  1. exceptions: SkillError.internal (debug-only) never reaches
     to_dict()/to_envelope(); an unexpected exception's message is
     wrapped, not dumped;
  2. approval: store + audit (extends GATE 6 to the audit path);
  3. audit: the dispatch error path scrubs error_internal before logging
     (this was a REAL leak — exc.internal was written raw to audit.jsonl;
     fixed in registry.py alongside this gate);
  4. idempotency: the store keeps params_hash only, never raw params;
  5. CLI: `idempotency list` prints slim records (no params/snapshots);
  6. MCP: call_tool error JSON contains no canary.

Accepted boundary (documented, not a leak): handler RESULT snapshots in
the idempotency store are stored as returned — they are the provider's
data, already delivered to the caller, inside the single-user local
trust boundary (see the threat model).
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from skillhub import approval as approval_mod
from skillhub import mock as mock_harness
from skillhub.audit import scrub_text
from skillhub.errors import SkillError, UpstreamError
from skillhub.registry import dispatch, load_registry

CANARY = "sk_live_G16canary9f8e7d6c5b4a"          # secret-shaped value
CANARY_KEY = "api_token"                          # secret-shaped key name
CANARY_NESTED = "sk_test_G16nested1a2b3c4d"       # nested secret shape


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    mock_harness.reset()
    return tmp_path


def _files_blob(isolated: Path) -> bytes:
    blob = b""
    for name in ("approvals.json", "audit.jsonl", "idempotency.json"):
        p = isolated / name
        if p.exists():
            blob += p.read_bytes()
    return blob


def _assert_no_canary(blob: bytes, where: str):
    for c in (CANARY, CANARY_NESTED):
        assert c.encode() not in blob, f"canary leaked in {where}"


# --- 1. exceptions ----------------------------------------------------------

def test_skill_error_internal_never_reaches_public_dict():
    # UpstreamError(skill, detail): detail lands in debug-only `internal`
    err = UpstreamError("someskill", f"boom: provider said {CANARY}")
    d = err.to_dict()
    _assert_no_canary(json.dumps(d).encode(), "SkillError.to_dict()")
    assert d["status"] == "error" and d["code"] == "upstream_error"
    assert CANARY in err.internal  # still available for local debugging


def test_unexpected_exception_message_is_wrapped_not_dumped(isolated):
    async def boom(method, url, **kw):
        raise RuntimeError(f"socket blew up carrying {CANARY}")

    mock_harness.enable()
    mock_harness.register("github", boom)
    reg = load_registry()
    import os
    os.environ["GITHUB_TOKEN"] = "mock"
    try:
        with pytest.raises(UpstreamError) as ei:
            asyncio.run(dispatch(
                reg["github"], "search_repositories", {"query": "x"}))
    finally:
        os.environ.pop("GITHUB_TOKEN", None)
        mock_harness.reset()
    d = ei.value.to_dict()
    assert d["status"] == "error"
    _assert_no_canary(json.dumps(d).encode(), "wrapped error dict")
    # the audit log got the scrubbed internal, not the raw canary
    _assert_no_canary(_files_blob(isolated), "audit.jsonl after wrap")
    assert b"[redacted]" in (isolated / "audit.jsonl").read_bytes()


def test_dispatch_error_audit_scrubs_internal(isolated):
    """The REAL leak this gate fixed: exc.internal hit audit.jsonl raw."""
    from skillhub import audit as audit_mod

    async def failer(method, url, **kw):
        # UpstreamError(skill, detail): detail is debug-only `internal`
        raise UpstreamError("github", f"provider 500 body contained {CANARY}")

    mock_harness.enable()
    mock_harness.register("github", failer)
    reg = load_registry()
    import os
    os.environ["GITHUB_TOKEN"] = "mock"
    try:
        with pytest.raises(UpstreamError) as ei:
            asyncio.run(dispatch(reg["github"], "search_repositories",
                                 {"query": "x"}))
    finally:
        os.environ.pop("GITHUB_TOKEN", None)
        mock_harness.reset()
    _assert_no_canary(json.dumps(ei.value.to_dict()).encode(),
                      "UpstreamError.to_dict()")
    blob = (isolated / "audit.jsonl").read_bytes()
    _assert_no_canary(blob, "audit.jsonl error_internal")
    assert b"[redacted]" in blob
    # the chain still verifies — scrubbing happens before hashing
    assert audit_mod.verify_chain()["ok"]


# --- 2. approval ------------------------------------------------------------

def test_approval_audit_path_has_no_canary(isolated):
    item = approval_mod.request_approval(
        "testskill", "do_thing",
        {"name": "visible", CANARY_KEY: CANARY,
         "nested": {"deep": CANARY_NESTED}},
        risk="write")
    _assert_no_canary(_files_blob(isolated), "approval store + audit log")
    approval_mod.approve(item["approval_id"])
    _assert_no_canary(_files_blob(isolated), "after approve")


# --- 3. idempotency ---------------------------------------------------------

def test_idempotency_store_keeps_hash_only(isolated):
    """Idempotency needs risk != read to reserve; use stripe's financial
    action through the real approval flow (same pattern as the contract
    test). The store must keep params_hash only — never raw params."""
    async def ok(method, url, **kw):
        return {"id": "plink_x", "url": "https://buy.stripe.com/x"}

    mock_harness.enable()
    mock_harness.register("stripe", ok)
    reg = load_registry()
    import os
    os.environ["STRIPE_SECRET_KEY"] = "mock-stripe-key"
    try:
        pending = approval_mod.request_approval(
            "stripe", "create_payment_link",
            {"product_name": f"Test {CANARY}", "amount_cents": 5000},
            risk="financial")
        approval_mod.approve(pending["approval_id"])
        asyncio.run(dispatch(
            reg["stripe"], "create_payment_link",
            {"product_name": f"Test {CANARY}", "amount_cents": 5000},
            approval_id=pending["approval_id"],
            idempotency_key="g16-key-1"))
    finally:
        os.environ.pop("STRIPE_SECRET_KEY", None)
        mock_harness.reset()
    blob = (isolated / "idempotency.json").read_bytes()
    _assert_no_canary(blob, "idempotency.json")
    stored = json.loads(blob)["g16-key-1"]
    assert stored["status"] == "succeeded"
    assert len(stored["params_hash"]) >= 32  # a hash, not the raw params


# --- 4. CLI -----------------------------------------------------------------

def test_cli_idempotency_list_prints_no_canary(isolated, capsys):
    from skillhub import cli as cli_mod
    old = sys.argv
    sys.argv = ["skillhub", "idempotency", "list"]
    try:
        assert cli_mod.idempotency() == 0
    finally:
        sys.argv = old
    _assert_no_canary(capsys.readouterr().out.encode(), "CLI list output")


def test_cli_unknown_command_echoes_nothing_secret(capsys):
    from skillhub import cli as cli_mod
    old = sys.argv
    sys.argv = ["skillhub", "bogus"]
    try:
        with pytest.raises(SystemExit):
            cli_mod.main()
    finally:
        sys.argv = old
    out = capsys.readouterr()
    _assert_no_canary((out.out + out.err).encode(), "CLI usage output")


# --- 5. MCP -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_tool_error_has_no_canary(isolated):
    from skillhub.server import call_tool

    async def failer(method, url, **kw):
        raise UpstreamError("github", f"provider 500 echo {CANARY}")

    mock_harness.enable()
    mock_harness.register("github", failer)
    import os
    os.environ["GITHUB_TOKEN"] = "mock"
    try:
        chunks = await call_tool(
            "github_search_repositories",
            {"query": f"x {CANARY}"})
    finally:
        os.environ.pop("GITHUB_TOKEN", None)
        mock_harness.reset()
    text = chunks[0].text
    payload = json.loads(text)
    assert payload["status"] == "error"
    assert payload["code"] == "upstream_error"
    _assert_no_canary(text.encode(), "MCP tool error JSON")


# --- scrub primitive --------------------------------------------------------

def test_scrub_text_catches_known_shapes():
    assert scrub_text(f"token={CANARY}") == "token=[redacted]"
    assert scrub_text("nothing secret here") == "nothing secret here"
    assert scrub_text(f"a {CANARY_NESTED} b") == "a [redacted] b"

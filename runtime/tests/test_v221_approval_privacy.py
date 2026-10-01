"""GATE 6 — approval data privacy: the secret canary MUST NOT LEAK.

A canary credential is planted in approval params (under a secret key
name, under an INNOCENT key name, nested, and via the explicit preview).
After requesting/approving, the canary must appear NOWHERE:
  - the approvals.json bytes on disk
  - approval.get() / list_pending() / approve() outputs
  - the ApprovalRequired exception preview surfaced to the caller
  - the audit log

Non-secret values must still be visible (redaction is surgical, not a
blanket wipe).

NOTE: canaries are assembled from parts at runtime so that no
secret-shaped literal ever sits in this source file.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from skillhub import approval, localstore
from skillhub.driver import ActionDef
from skillhub.errors import ApprovalRequired
from skillhub import registry


def _canary(kind: str) -> str:
    parts = {
        "stripe": ("sk_live_", "CANARY", "4f8a2b1c9d"),
        "github": ("ghp_", "CANARY", "0123456789abcdef0123"),
        "stripe_test": ("sk_test_", "CANARY", "nested7h6g5f"),
        "slack": ("xoxb-", "CANARY", "1234abcd"),
    }
    return "".join(parts[kind])


CANARY_KEY = _canary("stripe")
CANARY_VALUE_SHAPE = _canary("github")
CANARY_NESTED = _canary("stripe_test")
CANARY_PREVIEW = _canary("slack")

_ALL = (CANARY_KEY, CANARY_VALUE_SHAPE, CANARY_NESTED, CANARY_PREVIEW)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _store_bytes(isolated):
    p = isolated / "approvals.json"
    return p.read_bytes() if p.exists() else b""


def _audit_bytes(isolated):
    p = isolated / "audit.jsonl"
    return p.read_bytes() if p.exists() else b""


def _assert_no_canary(blob: bytes, where: str):
    for canary in _ALL:
        assert canary.encode() not in blob, f"canary leaked in {where}"


# --- engine-level: params + explicit preview -----------------------------------

def test_canary_never_persisted_raw(isolated):
    item = approval.request_approval(
        "testskill", "do_thing",
        {"name": "visible",
         "password": CANARY_KEY,                       # secret key name
         "note": CANARY_VALUE_SHAPE,                   # innocent key, secret shape
         "config": {"api_key": CANARY_NESTED}},         # nested secret
        risk="write",
        preview={"token": CANARY_PREVIEW},              # explicit preview
    )
    _assert_no_canary(_store_bytes(isolated), "approvals.json on disk")

    stored = approval.get(item["approval_id"])
    _assert_no_canary(json.dumps(stored).encode(), "approval.get()")
    assert stored["params_preview"]["name"] == "visible"
    assert stored["params_preview"]["password"] == "[redacted]"
    assert stored["params_preview"]["note"] == "[redacted]"
    assert stored["params_preview"]["config"]["api_key"] == "[redacted]"
    assert stored["preview"]["token"] == "[redacted]"

    pending = approval.list_pending()
    _assert_no_canary(json.dumps(pending).encode(), "list_pending()")

    approved = approval.approve(item["approval_id"])
    _assert_no_canary(json.dumps(approved).encode(), "approve() return")


def test_per_action_sensitive_params_redacted(isolated):
    item = approval.request_approval(
        "testskill", "do_thing",
        {"name": "visible", "customer_ref": "REF-999"},
        risk="write", extra_secret_keys=("customer_ref",))
    stored = approval.get(item["approval_id"])
    assert stored["params_preview"]["name"] == "visible"
    assert stored["params_preview"]["customer_ref"] == "[redacted]"
    _assert_no_canary(_store_bytes(isolated), "approvals.json on disk")


# --- dispatch-level: the full request flow -------------------------------------

def _secret_entry(handler):
    async def h(params):
        return await handler(params)
    ad = ActionDef(
        "test action",
        {"name": {"type": "string"}, "api_key": {"type": "string"}},
        ["name", "api_key"], h, write=True,
        sensitive_params=["api_key"],
    )
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True,
                               actions={"do_thing": ad})


def test_dispatch_approval_flow_leaks_nothing(isolated):
    async def handler(params):
        return {"ok": True}

    entry = _secret_entry(handler)
    with pytest.raises(ApprovalRequired) as ei:
        asyncio.run(registry.dispatch(
            entry, "do_thing",
            {"name": "visible", "api_key": CANARY_KEY},
            confirm=False))
    # the exception preview surfaced to the caller is redacted
    _assert_no_canary(json.dumps(ei.value.preview).encode(),
                      "ApprovalRequired.preview")
    assert ei.value.preview["api_key"] == "[redacted]"
    assert ei.value.preview["name"] == "visible"

    _assert_no_canary(_store_bytes(isolated), "approvals.json on disk")
    _assert_no_canary(_audit_bytes(isolated), "audit.jsonl")

    # approve + execute with the real params still works (hash binds them)
    item = approval.list_pending()[0]
    approval.approve(item["approval_id"])
    out = asyncio.run(registry.dispatch(
        entry, "do_thing",
        {"name": "visible", "api_key": CANARY_KEY},
        approval_id=item["approval_id"]))
    assert out["ok"] is True
    _assert_no_canary(_audit_bytes(isolated), "audit.jsonl after execute")


# --- redaction unit guarantees ---------------------------------------------------

def test_redact_params_shapes_and_recursion():
    from skillhub.audit import redact_params
    preview, h = redact_params({
        "password": "hunter2",
        "note": _canary("stripe"),
        "nested": {"list": [{"token": "zzz"}]},
        "long": "v" * 200,
        "plain": "hello",
    })
    assert preview["password"] == "[redacted]"
    assert preview["note"] == "[redacted]"
    assert preview["nested"]["list"][0]["token"] == "[redacted]"
    assert preview["long"].endswith("…[truncated]") and len(preview["long"]) < 200
    assert preview["plain"] == "hello"
    assert h.startswith("sha256:")

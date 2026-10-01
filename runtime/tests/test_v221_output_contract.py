"""GATE 7 — output contract.

Guarantees under test:
  1. Invalid output NEVER becomes an idempotency success: a handler whose
     result violates its output_schema gets the key marked FAILED (retry
     re-executes), never SUCCEEDED.
  2. Valid output commits; replays return the stored schema-conforming
     result without re-executing.
  3. A JSON-unsafe handler result (datetime, set, ...) cannot crash the
     idempotency commit: the store keeps a JSON snapshot, the caller keeps
     the original object.
  4. A secret that breaks the output contract does not leak through the
     violation detail into the audit log (jsonschema messages embed
     repr() of the offending value — they are scrubbed).

Canaries are assembled from parts at runtime so no secret-shaped literal
sits in this source file.
"""
from __future__ import annotations

import asyncio
import datetime
import json

import pytest

from skillhub import localstore, registry
from skillhub.driver import ActionDef
from skillhub.errors import OutputContractViolation


def _canary(kind: str) -> str:
    parts = {
        "stripe": ("sk_live_", "CANARY", "4f8a2b1c9d"),
        "github": ("ghp_", "CANARY", "0123456789abcdef0123"),
    }
    return "".join(parts[kind])


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    return asyncio.run(coro)


def _entry(handler, output_schema=None, **kwargs):
    async def h(params):
        return await handler(params)
    ad = ActionDef("test action", {"name": {"type": "string"}}, ["name"], h,
                   write=True, output_schema=output_schema, **kwargs)
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True,
                               actions={"do_thing": ad})


def _idem_status(isolated, key):
    p = isolated / "idempotency.json"
    return json.loads(p.read_text())["g7-" + key]["status"]


_SCHEMA = {"type": "object",
           "properties": {"n": {"type": "integer"}},
           "required": ["n"]}


# --- 1. invalid output must not become idempotency success ---------------------

def test_invalid_output_marks_failed_never_succeeded(isolated):
    calls = []

    async def handler(params):
        calls.append(1)
        if len(calls) == 1:
            return {"n": "not-an-integer"}  # violates output_schema
        return {"n": len(calls)}

    entry = _entry(handler, output_schema=_SCHEMA)
    with pytest.raises(OutputContractViolation):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g7-bad"))
    assert _idem_status(isolated, "bad") == "failed"
    assert len(calls) == 1

    # the retry path re-executes (exactly one retry, per the FAILED state)
    out = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                 confirm=True, idempotency_key="g7-bad"))
    assert out["n"] == 2 and len(calls) == 2
    assert _idem_status(isolated, "bad") == "succeeded"


def test_invalid_output_without_idempotency_key_still_raises(isolated):
    async def handler(params):
        return {"n": "nope"}

    entry = _entry(handler, output_schema=_SCHEMA)
    with pytest.raises(OutputContractViolation):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True))


# --- 2. valid output commits; replay is schema-conforming ----------------------

def test_valid_output_commits_and_replays(isolated):
    calls = []

    async def handler(params):
        calls.append(1)
        return {"n": len(calls)}

    entry = _entry(handler, output_schema=_SCHEMA)
    r1 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g7-good"))
    assert r1["n"] == 1
    assert _idem_status(isolated, "good") == "succeeded"
    r2 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g7-good"))
    assert r2["deduplicated"] is True and r2["n"] == 1 and len(calls) == 1


# --- 3. JSON-unsafe results cannot crash the commit ----------------------------

def test_json_unsafe_result_does_not_crash_commit(isolated):
    async def handler(params):
        return {"when": datetime.datetime(2026, 10, 2, 12, 0, 0),
                "tags": {"alpha", "beta"}}

    entry = _entry(handler)  # no output_schema: no constraints
    out = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                 confirm=True, idempotency_key="g7-exotic"))
    # the caller keeps the original objects
    assert isinstance(out["when"], datetime.datetime)
    assert out["tags"] == {"alpha", "beta"}
    # the store keeps a JSON snapshot — the write did not crash
    assert _idem_status(isolated, "exotic") == "succeeded"
    raw = json.loads((isolated / "idempotency.json").read_text())
    stored = raw["g7-exotic"]["result"]
    assert stored["when"] == "2026-10-02 12:00:00"
    # a set has no JSON form: it is str()-coerced (documented snapshot rule)
    assert isinstance(stored["tags"], str)
    assert "alpha" in stored["tags"] and "beta" in stored["tags"]
    # replay returns the snapshot without re-executing
    r2 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g7-exotic"))
    assert r2["deduplicated"] is True
    assert r2["when"] == "2026-10-02 12:00:00"


# --- 4. violation detail must not leak secrets into the audit log --------------

def test_output_violation_scrubs_secrets(isolated):
    canary = _canary("stripe")
    schema = {"type": "object",
              "properties": {"token": {"type": "integer"}},
              "required": ["token"]}

    async def handler(params):
        return {"token": canary}  # secret value, wrong type → violation

    entry = _entry(handler, output_schema=schema)
    with pytest.raises(OutputContractViolation) as ei:
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True))
    problems = json.dumps(ei.value.internal.get("problems", []))
    assert canary not in problems
    assert "[redacted]" in problems

    audit_bytes = (isolated / "audit.jsonl").read_bytes()
    assert canary.encode() not in audit_bytes


def test_validate_output_unit():
    from skillhub.validate import validate_output
    from skillhub.errors import OutputContractViolation
    schema = {"type": "object", "properties": {"a": {"type": "string"}},
              "required": ["a"], "additionalProperties": False}
    assert validate_output("s", "a", schema, {"a": "ok"}) == {"a": "ok"}
    assert validate_output("s", "a", {}, {"anything": 1}) == {"anything": 1}
    with pytest.raises(OutputContractViolation):
        validate_output("s", "a", schema, {"a": 1, "extra": True})

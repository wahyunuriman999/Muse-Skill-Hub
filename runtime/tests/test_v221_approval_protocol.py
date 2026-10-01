"""GATE 5 — approval protocol: theft and rebinding MUST FAIL.

The approval is bound to (skill, action, params_hash, risk, actor).
Exploit attempts that must fail:
  - theft: consume by a different actor than the requester
  - rebinding: reuse an approval for different params / action / skill
  - risk downgrade: a "write"-labelled approval blessing a "destructive"
    execution (and the reverse)
  - replay: double consume (also raced across real processes)
  - TTL: expired approvals
  - pending/denied approvals consumed directly

Plus: the MCP-facing request_approval driver must show the human the
registry-canonical risk, not a caller-supplied downgrade.
"""
from __future__ import annotations

import asyncio
import multiprocessing as mp

import pytest

from skillhub import approval, registry
from skillhub.driver import ActionDef
from skillhub.errors import ApprovalExpired, ApprovalRequired, ApprovalRevoked


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    return asyncio.run(coro)


def _entry(handler, risk="destructive", **kwargs):
    async def h(params):
        return await handler(params)
    ad = ActionDef("test action", {"name": {"type": "string"}}, ["name"], h,
                   write=True, risk=risk, **kwargs)
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True,
                               actions={"do_thing": ad,
                                        "other_thing": ad})


def _approved(skill="testskill", action="do_thing", params=None,
              risk="destructive", actor="local-user"):
    item = approval.request_approval(skill, action, params or {"name": "x"},
                                     risk=risk, actor=actor)
    approval.approve(item["approval_id"], approver=actor)
    return item


# --- theft --------------------------------------------------------------------

def test_approval_theft_by_different_actor_fails(isolated):
    item = _approved(actor="alice")
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "destructive", actor="mallory")
    # the failed theft did not burn the approval: alice can still use it
    out = approval.consume(item["approval_id"], "testskill", "do_thing",
                           {"name": "x"}, "destructive", actor="alice")
    assert out["status"] == "consumed"


def test_approval_theft_at_dispatch_fails(isolated):
    async def handler(params):
        return {"ok": True}

    entry = _entry(handler)
    item = _approved(actor="alice")
    with pytest.raises(ApprovalRevoked):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               approval_id=item["approval_id"],
                               actor="mallory"))


# --- rebinding -----------------------------------------------------------------

def test_approval_rebinding_params_fails(isolated):
    item = _approved(params={"name": "x"})
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "y"}, "destructive")


def test_approval_rebinding_action_fails(isolated):
    item = _approved(action="do_thing")
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "other_thing",
                         {"name": "x"}, "destructive")


def test_approval_rebinding_skill_fails(isolated):
    item = _approved(skill="testskill")
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "evilskill", "do_thing",
                         {"name": "x"}, "destructive")


def test_approval_rebinding_params_at_dispatch_fails(isolated):
    calls = []

    async def handler(params):
        calls.append(params["name"])
        return {"ok": True}

    entry = _entry(handler)
    item = _approved(params={"name": "x"})
    with pytest.raises(ApprovalRevoked):
        _run(registry.dispatch(entry, "do_thing", {"name": "MALICIOUS"},
                               approval_id=item["approval_id"]))
    assert calls == []  # the handler never ran


# --- risk binding ---------------------------------------------------------------

def test_approval_risk_downgrade_fails(isolated):
    """An approval labelled 'write' must never bless a 'destructive' run."""
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="write")
    approval.approve(item["approval_id"])
    with pytest.raises(ApprovalRevoked) as ei:
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "destructive")
    assert "risk" in str(ei.value)


def test_approval_risk_upgrade_also_fails_closed(isolated):
    """And a 'destructive' label cannot bless a 'write' run either —
    any mismatch fails closed."""
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="destructive")
    approval.approve(item["approval_id"])
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "write")


def test_approval_risk_downgrade_at_dispatch_fails(isolated):
    calls = []

    async def handler(params):
        calls.append(1)
        return {"ok": True}

    entry = _entry(handler, risk="destructive")
    # attacker requests the approval through the engine with a lying label
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="write")
    approval.approve(item["approval_id"])
    with pytest.raises(ApprovalRevoked):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               approval_id=item["approval_id"]))
    assert calls == []


# --- replay / TTL / state ---------------------------------------------------------

def test_double_consume_fails(isolated):
    item = _approved()
    approval.consume(item["approval_id"], "testskill", "do_thing",
                     {"name": "x"}, "destructive")
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "destructive")


def test_expired_approval_fails(isolated):
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="destructive", ttl_s=-1)
    with pytest.raises(ApprovalExpired):
        approval.approve(item["approval_id"])


def test_pending_approval_cannot_be_consumed(isolated):
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="destructive")
    with pytest.raises(ApprovalRequired):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "destructive")


def test_denied_approval_cannot_be_consumed(isolated):
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="destructive")
    approval.deny(item["approval_id"])
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "testskill", "do_thing",
                         {"name": "x"}, "destructive")


def test_unknown_approval_fails(isolated):
    with pytest.raises(ApprovalRequired):
        approval.consume("apr_nope", "testskill", "do_thing",
                         {"name": "x"}, "destructive")


def _race_worker(aid, q):
    from skillhub import approval as ap
    from skillhub.errors import ApprovalRevoked
    try:
        ap.consume(aid, "testskill", "do_thing", {"name": "x"},
                   "destructive")
        q.put("win")
    except ApprovalRevoked:
        q.put("loss")
    except Exception as exc:  # pragma: no cover - surfaced explicitly
        q.put(f"error:{type(exc).__name__}:{exc}")


def test_concurrent_consume_race_single_winner(isolated):
    """10 real processes race one approval → exactly 1 consumes it."""
    item = _approved()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    procs = [ctx.Process(target=_race_worker,
                         args=(item["approval_id"], q)) for _ in range(10)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    assert not any(p.exitcode for p in procs), "worker crashed"
    results = [q.get(timeout=10) for _ in procs]
    assert results.count("win") == 1, results
    assert results.count("loss") == 9, results


# --- the human sees the true risk -----------------------------------------------

def test_request_driver_shows_canonical_risk(isolated):
    """A caller-supplied risk downgrade must not reach the approver's eyes:
    the driver substitutes the registry-canonical risk."""
    import asyncio as _aio
    from skillhub.skills import permission_model

    reg = registry.load_registry()
    # gmail send_message is a real write-tier action in the catalog
    entry = reg.get("gmail")
    assert entry is not None and "send_message" in entry.actions
    out = _aio.run(permission_model.request_approval({
        "skill": "gmail", "action": "send_message",
        "params": {"to": "a@b.c"}, "risk": "read",  # lying downgrade
    }))
    item = out["approval"]
    from skillhub.policy import risk_for
    canonical = risk_for("gmail", "send_message",
                         entry.actions["send_message"].risk)
    assert item["risk"] == canonical != "read"
    # and that approval is consumable for the real risk tier
    approval.approve(item["approval_id"])
    out = approval.consume(item["approval_id"], "gmail", "send_message",
                           {"to": "a@b.c"}, canonical)
    assert out["status"] == "consumed"

"""GATE 4 — idempotency crash/replay semantics.

The DEFINED semantics (also documented in registry._idem_reserve):
  1. reserve-before-execute: concurrent processes → exactly one executes
     (proven with 20 spawn processes in test_v22_hardening.py).
  2. SUCCEEDED replay: same key+call → stored result, handler runs once.
  3. key reuse for a DIFFERENT call → IdempotencyConflict.
  4. FAILED → the retry path may claim it again.
  5. hard crash between reserve and commit → key stays PENDING; retries
     raise IdempotencyConflict (no silent double-execution, no silent
     success). The runtime NEVER auto-reclaims PENDING — it cannot tell
     "crashed" from "slow". Operator escape hatch: `skillhub idempotency
     release <key>` (audit-logged).
  6. crash after a provider side effect but before _idem_commit is NOT
     solved here — documented limitation, not a silent guarantee.

Tests 5 uses a real SIGKILL, not a mock.
"""
from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import os
import time

import pytest

from skillhub import localstore, registry
from skillhub.driver import ActionDef
from skillhub.errors import IdempotencyConflict, SkillError


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    return asyncio.run(coro)


def _entry(handler, **kwargs):
    async def h(params):
        return await handler(params)
    ad = ActionDef("test action", {"name": {"type": "string"}}, ["name"], h,
                   write=True, **kwargs)
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True,
                               actions={"do_thing": ad})


def _idem_path():
    return localstore.data_dir() / "idempotency.json"


def _read_idem():
    p = _idem_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# --- 2. success replay ---------------------------------------------------------

def test_success_replay_does_not_reexecute(isolated):
    calls = []

    async def handler(params):
        calls.append(1)
        return {"n": len(calls), "v": [1, 2, 3]}

    entry = _entry(handler)
    r1 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g4-replay"))
    assert r1["n"] == 1 and len(calls) == 1
    r2 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g4-replay"))
    assert r2["deduplicated"] is True
    assert r2["n"] == 1 and len(calls) == 1  # handler ran exactly once


def test_replay_result_is_a_snapshot(isolated):
    async def handler(params):
        return {"items": [1]}

    entry = _entry(handler)
    r1 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g4-snap"))
    r1["items"].append(999)  # caller mutates its copy
    r1["injected"] = True
    r2 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                confirm=True, idempotency_key="g4-snap"))
    assert r2["deduplicated"] is True
    assert r2["items"] == [1] and "injected" not in r2


# --- 3. key reuse for a different call ----------------------------------------

def test_key_reuse_for_different_params_conflicts(isolated):
    async def handler(params):
        return {"ok": True}

    entry = _entry(handler)
    _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                           confirm=True, idempotency_key="g4-reuse"))
    with pytest.raises(IdempotencyConflict):
        _run(registry.dispatch(entry, "do_thing", {"name": "DIFFERENT"},
                               confirm=True, idempotency_key="g4-reuse"))


# --- 4. failed → retry ---------------------------------------------------------

def test_failed_key_allows_exactly_the_retry_path(isolated):
    calls = []

    async def handler(params):
        calls.append(1)
        if len(calls) == 1:
            raise SkillError("testskill", "boom", "first attempt fails")
        return {"ok": True, "attempt": len(calls)}

    entry = _entry(handler)
    with pytest.raises(SkillError):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g4-fail"))
    assert _read_idem()["g4-fail"]["status"] == "failed"
    r = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g4-fail"))
    assert r["attempt"] == 2 and len(calls) == 2


# --- 5. hard crash between reserve and commit ---------------------------------

def _crash_worker(data_dir: str):
    """Reserve the key, then die mid-execution (handler blocks forever)."""
    import asyncio as _aio
    import os as _os
    _os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub import registry as _reg
    from skillhub.driver import ActionDef as _AD

    async def hanging(params):
        await _aio.sleep(60)
        return {"never": True}

    ad = _AD("hang", {"name": {"type": "string"}}, ["name"], hanging,
             write=True)
    entry = _reg.SkillEntry(name="testskill", description="t",
                            implemented=True, actions={"do_thing": ad})
    _aio.run(_reg.dispatch(entry, "do_thing", {"name": "x"}, confirm=True,
                           idempotency_key="g4-crash"))


def test_crash_between_reserve_and_commit_leaves_pending(isolated):
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_crash_worker, args=(str(isolated),))
    p.start()
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            rec = _read_idem().get("g4-crash")
            if rec and rec["status"] == "pending":
                break
            time.sleep(0.05)
        assert _read_idem()["g4-crash"]["status"] == "pending"
    finally:
        p.kill()  # SIGKILL mid-execution — no commit, no fail
        p.join(10)
        p.close()

    # the key is still PENDING: a retry must NOT silently re-execute
    async def handler(params):
        return {"ok": True}

    entry = _entry(handler)
    with pytest.raises(IdempotencyConflict) as ei:
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g4-crash"))
    assert "idempotency release" in str(ei.value)


def test_stale_pending_is_never_auto_reclaimed(isolated):
    """Even an ancient PENDING claim is not reclaimed by a retry — the
    runtime cannot tell 'crashed' from 'slow'."""
    owned, _ = registry._idem_reserve("g4-stale", "s", "a", "ph")
    assert owned
    # backdate the claim by a week
    store = localstore.data_dir() / "idempotency.json"
    data = json.loads(store.read_text(encoding="utf-8"))
    data["g4-stale"]["claimed_at"] -= 7 * 86400
    store.write_text(json.dumps(data), encoding="utf-8")

    async def handler(params):
        return {"ok": True}

    entry = _entry(handler)
    with pytest.raises(IdempotencyConflict):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g4-stale"))


def test_operator_release_unblocks_stuck_key(isolated):
    owned, _ = registry._idem_reserve("g4-rel", "s", "a", "ph")
    assert owned
    assert registry._idem_release("g4-rel") is True
    assert registry._idem_release("g4-rel") is False  # already gone

    calls = []

    async def handler(params):
        calls.append(1)
        return {"ok": True}

    entry = _entry(handler)
    r = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               confirm=True, idempotency_key="g4-rel"))
    assert r["ok"] is True and len(calls) == 1
    # the release was audit-logged
    trail = (localstore.data_dir() / "audit.jsonl").read_text(
        encoding="utf-8")
    assert "idempotency_release" in trail


def test_idempotency_cli_list_and_release(isolated):
    import subprocess
    import sys
    owned, _ = registry._idem_reserve("g4-cli", "s", "a", "ph")
    assert owned
    env = {**os.environ, "SKILLHUB_LOCAL_DIR": str(isolated)}
    out = subprocess.run(
        [sys.executable, "-m", "skillhub.cli", "idempotency", "list"],
        capture_output=True, text=True, env=env, cwd=".",
    )
    assert out.returncode == 0 and "g4-cli" in out.stdout
    out = subprocess.run(
        [sys.executable, "-m", "skillhub.cli", "idempotency", "release",
         "g4-cli"],
        capture_output=True, text=True, env=env, cwd=".",
    )
    assert out.returncode == 0 and "released" in out.stdout
    assert "g4-cli" not in _read_idem()

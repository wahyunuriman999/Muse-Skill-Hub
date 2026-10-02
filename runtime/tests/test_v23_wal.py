"""Tests for the v2.3 write-ahead log (skillhub/wal.py) and crash recovery.

The WAL narrows the idempotency crash window: instead of every stale
PENDING key being a manual mystery, recovery classifies them via the
phase history + owner-PID liveness.

- crashed BEFORE any external call (owner dead, no side_effect_started)
  → provably safe to reclaim (the started-record is fsync'd before the
  handler runs, so its absence proves the handler never ran)
- crashed DURING/AFTER the call (side_effect_started present, owner
  dead) → needs_reconciliation, NEVER auto-touched
- owner alive (or liveness inconclusive) → in_flight, untouched
- WAL unreadable → conservative: needs_reconciliation

No real crashes are needed for most tests: records are crafted with a
guaranteed-dead PID. One integration test uses a real subprocess that
reserves a key and exits (genuinely dead owner PID).
"""
import asyncio
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub import localstore, registry, wal
from skillhub.driver import ActionDef


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _write_idem(records: dict):
    p = localstore.data_dir() / "idempotency.json"
    p.write_text(json.dumps(records), encoding="utf-8")


def _read_idem() -> dict:
    p = localstore.data_dir() / "idempotency.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _pending(key, owner_pid, claimed_at=None):
    return {key: {"skill": "s", "action": "a", "params_hash": "ph",
                  "status": "pending", "result": None, "error_code": None,
                  "claimed_at": claimed_at or int(time.time()),
                  "owner_pid": owner_pid, "owner_token": "tok"}}


def _dead_pid() -> int:
    """A PID that is guaranteed not to exist on any platform."""
    return 2 ** 30


# --- classification ---------------------------------------------------------

def test_classify_reclaims_crash_before_side_effect(isolated):
    _write_idem(_pending("k1", _dead_pid()))
    wal.record("k1", wal.INTENT, skill="s", action="a", params_hash="ph")
    assert wal.classify("k1", _read_idem()["k1"]) == wal.SAFE_TO_RECLAIM


def test_classify_needs_reconciliation_after_side_effect_started(isolated):
    _write_idem(_pending("k2", _dead_pid()))
    wal.record("k2", wal.INTENT, skill="s", action="a", params_hash="ph")
    wal.record("k2", wal.SIDE_EFFECT_STARTED, skill="s", action="a",
               params_hash="ph")
    assert wal.classify("k2", _read_idem()["k2"]) == wal.NEEDS_RECONCILIATION


def test_classify_needs_reconciliation_after_side_effect_done(isolated):
    _write_idem(_pending("k3", _dead_pid()))
    for phase in (wal.INTENT, wal.SIDE_EFFECT_STARTED, wal.SIDE_EFFECT_DONE):
        wal.record("k3", phase, skill="s", action="a", params_hash="ph")
    assert wal.classify("k3", _read_idem()["k3"]) == wal.NEEDS_RECONCILIATION


def test_classify_leaves_live_owner_alone(isolated):
    _write_idem(_pending("k4", os.getpid()))
    assert wal.classify("k4", _read_idem()["k4"]) == wal.IN_FLIGHT


def test_classify_inconclusive_liveness_is_conservative(isolated, monkeypatch):
    _write_idem(_pending("k5", _dead_pid()))
    monkeypatch.setattr(wal, "pid_alive", lambda pid: None)
    assert wal.classify("k5", _read_idem()["k5"]) == wal.IN_FLIGHT


def test_classify_conservative_on_unreadable_wal(isolated):
    _write_idem(_pending("k6", _dead_pid()))
    (localstore.data_dir() / "wal.jsonl").write_text("not json {{{\n",
                                                     encoding="utf-8")
    assert wal.classify("k6", _read_idem()["k6"]) == wal.NEEDS_RECONCILIATION


def test_classify_settled_is_noop(isolated):
    rec = _pending("k7", _dead_pid())["k7"]
    rec["status"] = "succeeded"
    _write_idem({"k7": rec})
    assert wal.classify("k7", _read_idem()["k7"]) == wal.SETTLED


def test_classify_old_record_without_owner_pid(isolated):
    """v2.2 records have no owner_pid → liveness inconclusive → in_flight."""
    rec = _pending("k8", _dead_pid())["k8"]
    del rec["owner_pid"]
    _write_idem({"k8": rec})
    assert wal.classify("k8", _read_idem()["k8"]) == wal.IN_FLIGHT


# --- recovery ----------------------------------------------------------------

def test_recover_reclaims_and_rearms_retry(isolated):
    _write_idem(_pending("r1", _dead_pid()))
    wal.record("r1", wal.INTENT, skill="s", action="a", params_hash="ph")
    report = registry.idempotency_recover()
    assert report["reclaimed"] == ["r1"]
    rec = _read_idem()["r1"]
    assert rec["status"] == "failed"
    assert rec["error_code"] == "recovered_crash_before_side_effect"
    # the normal one-retry path now re-claims the key
    owned, _ = registry._idem_reserve("r1", "s", "a", "ph")
    assert owned is True


def test_recover_never_touches_post_side_effect(isolated):
    _write_idem(_pending("r2", _dead_pid()))
    wal.record("r2", wal.SIDE_EFFECT_STARTED, skill="s", action="a",
               params_hash="ph")
    report = registry.idempotency_recover()
    assert report["reclaimed"] == []
    assert len(report["needs_reconciliation"]) == 1
    info = report["needs_reconciliation"][0]
    assert info["idempotency_key"] == "r2"
    assert wal.SIDE_EFFECT_STARTED in info["wal_phases"]
    assert _read_idem()["r2"]["status"] == "pending"  # untouched


def test_recover_dry_run_changes_nothing(isolated):
    _write_idem(_pending("r3", _dead_pid()))
    report = registry.idempotency_recover(apply=False)
    assert report["dry_run"] is True
    assert report["reclaimed"] == ["r3"]
    assert _read_idem()["r3"]["status"] == "pending"  # untouched


def test_recover_mixed_batch(isolated):
    _write_idem({
        **_pending("m1", _dead_pid()),
        **_pending("m2", _dead_pid()),
        **_pending("m3", os.getpid()),
    })
    wal.record("m1", wal.INTENT)
    wal.record("m2", wal.SIDE_EFFECT_STARTED)
    report = registry.idempotency_recover()
    assert report["reclaimed"] == ["m1"]
    assert [i["idempotency_key"] for i in report["needs_reconciliation"]] == ["m2"]
    assert report["in_flight"] == ["m3"]


# --- dispatch integration: phases are actually recorded -----------------------

def _entry(handler):
    ad = ActionDef("t", {"x": {"type": "string"}}, [], handler, write=True)
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True, actions={"do": ad})


def test_dispatch_records_wal_phases(isolated, monkeypatch):
    monkeypatch.setenv("TESTWAL_TOKEN", "x")  # silence credential checks

    async def handler(params):
        return {"ok": True}

    async def go():
        # bypass credential/policy layers: call the phase-relevant core
        # through a real dispatch with confirm=True on a no-env skill
        return await registry.dispatch(
            _entry(handler), "do", {"x": "1"}, confirm=True,
            idempotency_key="w1")

    # the test skill has no required_env, so dispatch runs fully
    out = asyncio.run(go())
    assert out["ok"] is True
    phases = wal.phases_for("w1")
    assert phases == [wal.INTENT, wal.SIDE_EFFECT_STARTED, wal.SIDE_EFFECT_DONE]
    rec = _read_idem()["w1"]
    assert rec["status"] == "succeeded"
    assert rec["owner_pid"] == os.getpid()


def test_dispatch_without_key_writes_no_wal(isolated):
    async def handler(params):
        return {"ok": True}

    asyncio.run(registry.dispatch(_entry(handler), "do", {"x": "1"},
                                  confirm=True))
    assert wal.phases_for("nope") == []
    assert not (localstore.data_dir() / "wal.jsonl").exists()


# --- real subprocess crash -----------------------------------------------------

def _reserve_and_die(data_dir: str):
    """Reserve a key in a child process, then exit without commit/fail."""
    os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub import registry as _reg
    _reg._idem_reserve("crash-key", "someskill", "someaction", "ph123")
    # write the intent the way dispatch would, then die mid-flight
    from skillhub import wal as _wal
    _wal.record("crash-key", _wal.INTENT, skill="someskill",
                action="someaction", params_hash="ph123")
    os._exit(0)  # noqa: PGH — deliberate hard crash, no cleanup


def test_recover_reclaims_real_crashed_process(isolated):
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_reserve_and_die, args=(str(isolated),))
    p.start()
    p.join(20)
    assert p.exitcode == 0
    dead_pid = p.pid
    assert wal.pid_alive(dead_pid) is False  # genuinely dead

    rec = _read_idem()["crash-key"]
    assert rec["status"] == "pending"
    assert rec["owner_pid"] == dead_pid

    report = registry.idempotency_recover()
    assert report["reclaimed"] == ["crash-key"]
    assert _read_idem()["crash-key"]["status"] == "failed"


def test_pid_alive_self_and_nonsense():
    assert wal.pid_alive(os.getpid()) is True
    assert wal.pid_alive(_dead_pid()) is False
    assert wal.pid_alive(None) is None
    assert wal.pid_alive(-5) is None
    assert wal.pid_alive("not-a-pid") is None


def test_prune_keeps_pending_drops_old_settled(isolated):
    _write_idem({**_pending("p1", _dead_pid()),
                 **_pending("p2", _dead_pid())})
    # p2 settles; both get old WAL records
    _read_idem()["p2"]["status"] = "succeeded"
    _write_idem({k: {**v, "status": "succeeded"} if k == "p2" else v
                 for k, v in _read_idem().items()})
    old_ts = int(time.time()) - 10 * 86400
    p = localstore.data_dir() / "wal.jsonl"
    p.write_text(
        json.dumps({"ts": old_ts, "key": "p1", "phase": "intent",
                    "pid": 1, "owner": "o"}) + "\n"
        + json.dumps({"ts": old_ts, "key": "p2", "phase": "intent",
                      "pid": 1, "owner": "o"}) + "\n",
        encoding="utf-8")
    dropped = wal.prune(max_age_days=7)
    assert dropped == 1  # only the settled key's record
    assert wal.phases_for("p1") == ["intent"]
    assert wal.phases_for("p2") == []

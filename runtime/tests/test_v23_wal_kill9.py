"""GATE 23 — WAL crash recovery under a real SIGKILL (kill -9).

test_v23_wal.py proves classification and recovery with crafted records and
one graceful subprocess exit. These tests go further: a REAL child process
is SIGKILLed mid-flight at each WAL phase, so the parent can never rely on
cooperative cleanup. Recovery must then:

- kill after INTENT only → safe_to_reclaim; reclaimed as FAILED exactly
  once; a second recover() is a no-op for that key (proves exactly-once
  reclaim, no double-reclaim);
- kill after INTENT + SIDE_EFFECT_STARTED → needs_reconciliation and the
  record is NEVER auto-touched (proven over two recover() runs);
- kill after all three phases → needs_reconciliation, untouched.

Each child reserves its key and records WAL phases exactly the way
dispatch does (fsync'd before the next step), signals readiness to the
parent, then blocks — the parent SIGKILLs it, so the PID is genuinely
dead with no chance of atexit/finally handlers running.

POSIX-only (SIGKILL); total runtime is a few seconds.
"""
import json
import multiprocessing as mp
import os
import signal
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub import localstore, registry, wal

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="SIGKILL kill -9 tests are POSIX-only")


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _read_idem() -> dict:
    p = localstore.data_dir() / "idempotency.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _crash_at_phase(data_dir: str, key: str, phases: list):
    """Child: reserve a key, durably record WAL phases, then hang.

    The parent SIGKILLs this process after it signals readiness, so no
    cleanup code here ever runs — a genuine hard crash.
    """
    os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub import localstore as _ls
    from skillhub import registry as _reg
    from skillhub import wal as _wal

    owned, _ = _reg._idem_reserve(key, "kill9skill", "kill9action", "ph-kill9")
    assert owned, "child failed to reserve its idempotency key"
    for phase in phases:
        _wal.record(key, phase, skill="kill9skill", action="kill9action",
                    params_hash="ph-kill9")
    # Ready only AFTER every phase is fsync'd: the parent must never kill
    # us before the WAL evidence is durable.
    (_ls.data_dir() / f"ready-{key}").write_text("ready", encoding="utf-8")
    while True:
        time.sleep(1)  # killed by the parent; never returns


def _spawn_and_sigkill(data_dir: Path, key: str, phases: list) -> int:
    """Run the child, wait for readiness, SIGKILL it; return its dead PID."""
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_crash_at_phase,
                    args=(str(data_dir), key, list(phases)))
    p.start()
    try:
        ready = data_dir / f"ready-{key}"
        deadline = time.time() + 20
        while not ready.exists():
            assert time.time() < deadline, "child never signalled readiness"
            assert p.is_alive(), "child died before signalling readiness"
            time.sleep(0.05)
        child_pid = p.pid
        os.kill(child_pid, signal.SIGKILL)
        p.join(10)
        if p.is_alive():
            p.terminate()
            pytest.fail("child survived SIGKILL")
        assert p.exitcode == -signal.SIGKILL, \
            f"child exitcode {p.exitcode}, expected SIGKILL (-{signal.SIGKILL})"
        return child_pid
    finally:
        if p.is_alive():
            p.terminate()


def _needs_reconciliation_entry(report: dict, key: str) -> dict:
    hits = [i for i in report["needs_reconciliation"]
            if i["idempotency_key"] == key]
    assert hits, f"{key} missing from needs_reconciliation"
    return hits[0]


def test_kill9_before_side_effect_reclaimed_exactly_once(isolated):
    """SIGKILL after INTENT only → reclaimed as FAILED exactly once."""
    key = "kill9-intent"
    dead_pid = _spawn_and_sigkill(isolated, key, [wal.INTENT])

    assert wal.pid_alive(dead_pid) is False  # genuinely dead
    rec = _read_idem()[key]
    assert rec["status"] == "pending"
    assert rec["owner_pid"] == dead_pid
    # the fsync'd WAL survived the crash and drives the verdict
    assert wal.phases_for(key) == [wal.INTENT]
    assert wal.classify(key, rec) == wal.SAFE_TO_RECLAIM

    report1 = registry.idempotency_recover()
    assert report1["reclaimed"] == [key]
    rec = _read_idem()[key]
    assert rec["status"] == "failed"
    assert rec["error_code"] == "recovered_crash_before_side_effect"

    # second recover() must be a no-op for this key: exactly-once reclaim
    report2 = registry.idempotency_recover()
    assert report2["reclaimed"] == []
    assert report2["needs_reconciliation"] == []
    rec2 = _read_idem()[key]
    assert rec2["status"] == "failed"
    assert rec2["error_code"] == "recovered_crash_before_side_effect"


def test_kill9_during_side_effect_never_touched(isolated):
    """SIGKILL after SIDE_EFFECT_STARTED → needs_reconciliation, untouched."""
    key = "kill9-started"
    dead_pid = _spawn_and_sigkill(
        isolated, key, [wal.INTENT, wal.SIDE_EFFECT_STARTED])

    assert wal.pid_alive(dead_pid) is False
    rec = _read_idem()[key]
    assert rec["status"] == "pending"
    assert wal.classify(key, rec) == wal.NEEDS_RECONCILIATION

    for _ in range(2):  # run twice: recovery must never auto-touch it
        report = registry.idempotency_recover()
        assert report["reclaimed"] == []
        info = _needs_reconciliation_entry(report, key)
        assert wal.SIDE_EFFECT_STARTED in info["wal_phases"]
        rec = _read_idem()[key]
        assert rec["status"] == "pending"      # untouched
        assert rec["error_code"] is None      # untouched
        assert rec["owner_pid"] == dead_pid   # untouched


def test_kill9_after_side_effect_done_never_touched(isolated):
    """SIGKILL after SIDE_EFFECT_DONE → needs_reconciliation, untouched."""
    key = "kill9-done"
    dead_pid = _spawn_and_sigkill(
        isolated, key,
        [wal.INTENT, wal.SIDE_EFFECT_STARTED, wal.SIDE_EFFECT_DONE])

    assert wal.pid_alive(dead_pid) is False
    rec = _read_idem()[key]
    assert rec["status"] == "pending"
    assert wal.phases_for(key) == [wal.INTENT, wal.SIDE_EFFECT_STARTED,
                                   wal.SIDE_EFFECT_DONE]
    assert wal.classify(key, rec) == wal.NEEDS_RECONCILIATION

    for _ in range(2):
        report = registry.idempotency_recover()
        assert report["reclaimed"] == []
        info = _needs_reconciliation_entry(report, key)
        assert wal.SIDE_EFFECT_DONE in info["wal_phases"]
        rec = _read_idem()[key]
        assert rec["status"] == "pending"
        assert rec["error_code"] is None
        assert rec["owner_pid"] == dead_pid

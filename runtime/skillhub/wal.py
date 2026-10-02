"""Write-ahead intent log for the idempotency crash window (v2.3).

The idempotency store alone cannot distinguish three situations for a
stale PENDING key:

  1. another process is still running it         → must not touch
  2. the owner crashed BEFORE any external call → safe to reclaim
  3. the owner crashed DURING/AFTER the call    → outcome unknown

The WAL records fine-grained phases for every idempotent execution —
``intent`` → ``side_effect_started`` → ``side_effect_done`` — each
appended with ``fsync`` *before* the next step runs. Crash recovery
combines the phase history with owner-PID liveness to *classify* stale
keys instead of forcing all of them through manual operator review.

Ordering guarantee (the whole point): ``side_effect_started`` is
durably recorded before the action handler is invoked. Its *absence*
therefore proves the handler never ran, which makes reclaiming
case (2) provably safe — no double execution is possible.

Honest boundary (unchanged from v2.2): this does NOT make an external
call atomic with the local commit. Exactly-once across a crash remains
impossible for arbitrary providers; case (3) is reported as
``needs_reconciliation`` for a human, never auto-retried. What the WAL
buys is machine-classified recovery instead of "every stale key is a
manual mystery".

PID-reuse caveat: if the OS recycles the owner's PID for an unrelated
process, liveness errs *conservative* (a live-looking PID is treated as
in-flight, never reclaimed). The dangerous direction — a live owner
misread as dead — cannot happen from PID reuse alone.
"""
from __future__ import annotations

import json
import os
import time
import uuid

from . import filelock, localstore

_WAL_NAME = "wal"
_OWNER_TOKEN = uuid.uuid4().hex  # unique per process; disambiguates reclaims

# Phases, in lifecycle order.
INTENT = "intent"
SIDE_EFFECT_STARTED = "side_effect_started"
SIDE_EFFECT_DONE = "side_effect_done"

# Classification outcomes for a stale PENDING idempotency record.
IN_FLIGHT = "in_flight"                    # owner alive (or liveness unknown) — do not touch
SAFE_TO_RECLAIM = "safe_to_reclaim"        # owner dead, handler provably never ran
NEEDS_RECONCILIATION = "needs_reconciliation"  # owner dead after/during side effect — human decides
SETTLED = "settled"                        # not PENDING anymore; nothing to do


def _wal_path():
    return localstore.data_dir() / f"{_WAL_NAME}.jsonl"


def _wal_lock():
    return localstore.data_dir() / f"{_WAL_NAME}.lock"


def record(key: str, phase: str, *, skill: str = "", action: str = "",
           params_hash: str = "") -> None:
    """Durably append one phase record (fsync before return)."""
    localstore.append_jsonl(_WAL_NAME, {
        "ts": int(time.time()),
        "key": key,
        "phase": phase,
        "pid": os.getpid(),
        "owner": _OWNER_TOKEN,
        "skill": skill,
        "action": action,
        "params_hash": params_hash,
    })


def _read_all() -> list[dict] | None:
    """All WAL records, or None when the log is missing/unreadable.

    A missing log is normal (no idempotent writes yet) → []. An
    *unreadable* log is abnormal → None, and recovery must stay
    conservative for every stale key.
    """
    p = _wal_path()
    if not p.exists():
        return []
    try:
        with filelock.locked(_wal_lock()):
            lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    out: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            return None  # torn/corrupt log → conservative
    return out


def phases_for(key: str) -> list[str] | None:
    """Phase history for one idempotency key, or None if unreadable."""
    records = _read_all()
    if records is None:
        return None
    return [r["phase"] for r in records if r.get("key") == key]


def pid_alive(pid) -> bool | None:
    """True/False/None(inconclusive) — cross-process liveness probe.

    None is returned when the platform cannot answer (rather than
    guessing); callers must treat None as alive (conservative).
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by another user → alive
    except OSError:
        return None  # platform cannot answer → inconclusive
    else:
        return True


def owner_token() -> str:
    """This process's unique owner token (stored on PENDING records)."""
    return _OWNER_TOKEN


def classify(key: str, record: dict) -> str:
    """Classify one idempotency record. See module docstring for semantics."""
    if record.get("status") != "pending":
        return SETTLED
    alive = pid_alive(record.get("owner_pid"))
    if alive is not False:
        # Owner alive, or the platform cannot tell → never touch.
        return IN_FLIGHT
    phases = phases_for(key)
    if phases is None:
        return NEEDS_RECONCILIATION  # cannot prove anything → human decides
    if SIDE_EFFECT_STARTED in phases:
        return NEEDS_RECONCILIATION  # the call may have happened → human decides
    # Owner is dead and the handler provably never ran (the
    # side_effect_started record is written before the handler is
    # invoked, so its absence is proof). Safe to reclaim.
    return SAFE_TO_RECLAIM


def prune(max_age_days: int = 7, keep_pending: bool = True) -> int:
    """Drop WAL records that can no longer affect recovery.

    Removes records for keys with no PENDING idempotency record left,
    older than ``max_age_days``. Returns the number of records removed.
    Never removes records for keys that are still PENDING.
    """
    records = _read_all()
    if not records:
        return 0
    cutoff = int(time.time()) - max_age_days * 86400
    try:
        data = localstore.read_json("idempotency", {})
        pending_keys = {k for k, v in data.items()
                        if isinstance(v, dict) and v.get("status") == "pending"}
    except Exception:
        return 0  # store unreadable → do not prune
    keep: list[dict] = []
    dropped = 0
    for r in records:
        if (keep_pending and r.get("key") in pending_keys) or r.get("ts", 0) >= cutoff:
            keep.append(r)
        else:
            dropped += 1
    if dropped:
        p = _wal_path()
        tmp = p.with_name(f"{p.name}.tmp.{os.getpid()}")
        with filelock.locked(_wal_lock()):
            with open(tmp, "w", encoding="utf-8") as fh:
                for r in keep:
                    fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, p)
    return dropped

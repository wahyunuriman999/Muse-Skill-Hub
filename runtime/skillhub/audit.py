"""Audit log — every executed action is recorded, secrets never are.

Each record::

    {
      "event_id": "evt_…",
      "timestamp": 1727…,
      "request_id": "9f2c…",
      "actor": "local-user",
      "skill": "gmail",
      "action": "send_message",
      "risk": "communication",
      "params_hash": "sha256:…",
      "params_preview": {"to": "a@b.c"},   # non-sensitive preview only
      "approval_id": "apr_…",
      "idempotency_key": "…",
      "result": "success",
      "error_code": null,
      "duration_ms": 842
    }

Redaction: parameter VALUES are never stored raw except for a small preview
of non-sensitive keys. Anything whose key looks like a secret
(password, token, secret, api_key, card, ssn, …) is replaced with
"[redacted]" and only its sha256 is kept. Full internal error details are
kept in the log (never sent to the LLM).

Stored append-only in ``~/.skillhub-local/audit.jsonl``.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from . import localstore

_STORE = "audit"

_SECRET_HINTS = ("password", "passwd", "secret", "token", "api_key", "apikey",
                 "private_key", "card", "cvv", "ssn", "bearer", "credential",
                 "auth", "session")


def _is_secret_key(key: str) -> bool:
    k = key.lower()
    return any(h in k for h in _SECRET_HINTS)


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


def redact_params(params: dict, extra_secret_keys: tuple = ()) -> tuple[dict, str]:
    """Return (preview, params_hash). Secrets are redacted from the preview."""
    preview: dict = {}
    for key, value in (params or {}).items():
        if _is_secret_key(key) or key in extra_secret_keys:
            preview[key] = "[redacted]"
        elif isinstance(value, str) and len(value) > 120:
            preview[key] = value[:120] + "…[truncated]"
        else:
            preview[key] = value
    params_hash = "sha256:" + hashlib.sha256(
        json.dumps(params or {}, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return preview, params_hash


def _canonical(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


def _event_hash(record: dict) -> str:
    return "sha256:" + hashlib.sha256(_canonical(record)).hexdigest()[:32]


def log(record: dict) -> dict:
    """Append an audit event with a tamper-evident hash chain.

    Each event carries ``prev_hash`` (the previous event's hash, or
    ``"GENESIS"``) and ``event_hash``. The read of the previous hash and
    the append happen under one exclusive lock, so concurrent writers
    cannot fork the chain. This detects tampering (edit/delete/reorder)
    — it does not prevent a filesystem-level attacker from rewriting the
    whole file, which no local log can. For stronger guarantees, ship the
    log to a WORM / remote append-only store.
    """
    from . import localstore as _ls

    record = {
        "event_id": "evt_" + uuid.uuid4().hex[:12],
        "timestamp": int(time.time()),
        **record,
    }
    path = _ls.data_dir() / f"{_STORE}.jsonl"
    with _ls.locked(path, "a+") as fh:
        fh.seek(0)
        prev_hash = "GENESIS"
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                prev_hash = json.loads(line).get("event_hash", prev_hash)
            except json.JSONDecodeError:
                continue
        record["prev_hash"] = prev_hash
        record["event_hash"] = _event_hash(
            {k: v for k, v in record.items() if k != "event_hash"})
        fh.seek(0, 2)  # a+ mode: ensure we're at the end before writing
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        fh.flush()
        try:
            import os
            os.fsync(fh.fileno())
            os.chmod(path, 0o600)
        except OSError:
            pass
    return record


def verify_chain() -> dict:
    """Verify the audit hash chain. Returns a report dict.

    Checks every chained event: hash recomputation and prev_hash linkage.
    Legacy events (written before chaining) are counted, not failed.
    """
    from . import localstore as _ls

    path = _ls.data_dir() / f"{_STORE}.jsonl"
    report = {"events": 0, "chained": 0, "legacy": 0, "ok": True,
              "first_bad": None}
    if not path.exists():
        return report
    prev_hash = "GENESIS"
    with _ls.shared_locked(path, "r") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            report["events"] += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "event_hash" not in rec:
                report["legacy"] += 1
                continue
            report["chained"] += 1
            if rec.get("prev_hash") != prev_hash:
                report["ok"] = False
                report["first_bad"] = {"line": lineno, "reason": "prev_hash mismatch"}
                break
            recomputed = _event_hash(
                {k: v for k, v in rec.items() if k != "event_hash"})
            if recomputed != rec["event_hash"]:
                report["ok"] = False
                report["first_bad"] = {"line": lineno, "reason": "event_hash mismatch"}
                break
            prev_hash = rec["event_hash"]
    return report


def query(limit: int = 50, skill: str = "", action: str = "",
          result: str = "") -> list[dict]:
    """Read the audit log newest-first, with optional filters."""
    from . import localstore as _ls

    path = _ls.data_dir() / f"{_STORE}.jsonl"
    if not path.exists():
        return []
    rows: list[dict] = []
    with _ls.shared_locked(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if skill:
        rows = [r for r in rows if r.get("skill") == skill]
    if action:
        rows = [r for r in rows if r.get("action") == action]
    if result:
        rows = [r for r in rows if r.get("result") == result]
    rows.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    return rows[:max(1, min(limit, 500))]

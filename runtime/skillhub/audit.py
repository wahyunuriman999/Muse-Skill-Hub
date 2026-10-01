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


def log(record: dict) -> dict:
    record = {
        "event_id": "evt_" + uuid.uuid4().hex[:12],
        "timestamp": int(time.time()),
        **record,
    }
    localstore.append_jsonl(_STORE, record)
    return record


def query(limit: int = 50, skill: str = "", action: str = "",
          result: str = "") -> list[dict]:
    """Read the audit log newest-first, with optional filters."""
    path = localstore.data_dir() / f"{_STORE}.jsonl"
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, encoding="utf-8") as fh:
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

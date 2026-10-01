"""Approval engine — production-grade human-in-the-loop.

A write action never executes on a bare ``confirm=true`` boolean alone in
production mode. Instead:

1. LLM (or runtime) calls ``request_approval(skill, action, params)``
   → returns ``approval_id`` (``apr_…``), status ``pending``.
2. A human approves/denies (MCP tool, CLI, or UI).
3. ``dispatch(..., approval_id="apr_…")`` validates before executing:
   - same skill, same action, same parameters (sha256-bound)
   - not expired (default TTL 10 minutes)
   - not already consumed (single-use)
   - not revoked/denied

Approvals persist in ``~/.skillhub-local/approvals.json`` (atomic writes,
override with SKILLHUB_LOCAL_DIR).
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid

from . import localstore
from .errors import ApprovalExpired, ApprovalRequired, ApprovalRevoked

_STORE = "approvals"
DEFAULT_TTL_S = 600


def _params_hash(params: dict) -> str:
    canonical = json.dumps(params or {}, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load() -> dict:
    return localstore.read_json(_STORE, {"approvals": {}})


def _save(data: dict) -> None:
    localstore.write_json(_STORE, data)


def request_approval(skill: str, action: str, params: dict,
                     risk: str = "write", ttl_s: int = DEFAULT_TTL_S,
                     actor: str = "local-user", preview: dict | None = None) -> dict:
    data = _load()
    approval_id = "apr_" + uuid.uuid4().hex[:12]
    now = int(time.time())
    item = {
        "approval_id": approval_id,
        "skill": skill,
        "action": action,
        "params": params or {},
        "params_hash": _params_hash(params),
        "risk": risk,
        "status": "pending",
        "actor": actor,
        "preview": preview or {},
        "created_at": now,
        "expires_at": now + ttl_s,
        "consumed_at": None,
    }
    data["approvals"][approval_id] = item
    _save(data)
    return item


def get(approval_id: str) -> dict | None:
    return _load()["approvals"].get(approval_id)


def list_pending() -> list[dict]:
    now = int(time.time())
    return [a for a in _load()["approvals"].values()
            if a["status"] == "pending" and a["expires_at"] > now]


def approve(approval_id: str, approver: str = "local-user") -> dict:
    data = _load()
    item = data["approvals"].get(approval_id)
    if not item:
        raise ApprovalRevoked(f"Unknown approval '{approval_id}'.")
    now = int(time.time())
    if item["status"] != "pending":
        raise ApprovalRevoked(f"Approval '{approval_id}' is {item['status']}.")
    if item["expires_at"] <= now:
        item["status"] = "expired"
        _save(data)
        raise ApprovalExpired(f"Approval '{approval_id}' expired.")
    item["status"] = "approved"
    item["approved_by"] = approver
    item["approved_at"] = now
    _save(data)
    return item


def deny(approval_id: str, approver: str = "local-user") -> dict:
    data = _load()
    item = data["approvals"].get(approval_id)
    if not item:
        raise ApprovalRevoked(f"Unknown approval '{approval_id}'.")
    if item["status"] != "pending":
        raise ApprovalRevoked(f"Approval '{approval_id}' is {item['status']}.")
    item["status"] = "denied"
    item["approved_by"] = approver
    _save(data)
    return item


def consume(approval_id: str, skill: str, action: str, params: dict) -> dict:
    """Validate and single-use consume an approval. Raises on any mismatch."""
    data = _load()
    item = data["approvals"].get(approval_id)
    if not item:
        raise ApprovalRequired(skill, action,
                               {"reason": f"unknown approval '{approval_id}'"})
    now = int(time.time())
    if item["status"] == "pending":
        raise ApprovalRequired(
            skill, action,
            {"reason": f"approval '{approval_id}' is still pending"})
    if item["status"] in ("denied", "revoked"):
        raise ApprovalRevoked(f"Approval '{approval_id}' was {item['status']}.")
    if item["status"] == "consumed":
        raise ApprovalRevoked(f"Approval '{approval_id}' was already consumed.")
    if item["expires_at"] <= now:
        item["status"] = "expired"
        _save(data)
        raise ApprovalExpired(f"Approval '{approval_id}' expired.")
    if item["status"] != "approved":
        raise ApprovalRevoked(f"Approval '{approval_id}' is {item['status']}.")
    # parameter binding: the approval covers EXACTLY these params
    if (item["skill"], item["action"]) != (skill, action) or \
            item["params_hash"] != _params_hash(params):
        raise ApprovalRevoked(
            f"Approval '{approval_id}' does not match this skill/action/parameters.")
    item["status"] = "consumed"
    item["consumed_at"] = now
    _save(data)
    return item

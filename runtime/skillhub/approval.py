"""Approval engine — human-in-the-loop with atomic single-use consumption.

A write action never executes on a bare ``confirm=true`` boolean alone in
production mode. Instead:

1. LLM (or runtime) calls ``request_approval(skill, action, params)``
   → returns ``approval_id`` (``apr_…``), status ``pending``.
2. A human approves/denies (MCP tool, CLI, or UI).
3. ``dispatch(..., approval_id="apr_…")`` validates before executing:
   - same skill, same action, same parameters (sha256-bound)
   - same actor (the principal that requested must be the one executing)
   - not expired (default TTL 10 minutes)
   - not already consumed — **atomically**: the check and the
     ``approved → consumed`` transition happen inside ONE file-locked
     critical section, so two concurrent processes cannot both consume
     the same approval.

Approvals persist in ``~/.skillhub-local/approvals.json`` (override with
SKILLHUB_LOCAL_DIR). This is a single-user local runtime boundary: there
is no multi-tenant identity here — ``actor`` is a session label, and the
guarantee is "the same actor that requested is the one that executes",
not cryptographic authentication.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid

from . import localstore
from .audit import redact_params
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
    with localstore.locked_json(_STORE, {"approvals": {}}) as data:
        approvals = data.setdefault("approvals", {})
        approval_id = "apr_" + uuid.uuid4().hex[:12]
        now = int(time.time())
        # The store NEVER keeps raw params: only the binding hash plus a
        # redacted preview (secrets → "[redacted]"). Execution re-supplies
        # the real params and consume() verifies them against params_hash.
        params_preview, _ = redact_params(params or {})
        item = {
            "approval_id": approval_id,
            "skill": skill,
            "action": action,
            "params_hash": _params_hash(params),
            "params_preview": params_preview,
            "risk": risk,
            "status": "pending",
            "actor": actor,
            "preview": preview or {},
            "created_at": now,
            "expires_at": now + ttl_s,
            "consumed_at": None,
        }
        approvals[approval_id] = item
        return dict(item)


def get(approval_id: str) -> dict | None:
    item = _load()["approvals"].get(approval_id)
    return dict(item) if item else None


def list_pending() -> list[dict]:
    now = int(time.time())
    return [a for a in _load()["approvals"].values()
            if a["status"] == "pending" and a["expires_at"] > now]


def _transition(approval_id: str, approver: str, to_status: str) -> dict:
    """Atomic pending → approved/denied transition (single critical section)."""
    with localstore.locked_json(_STORE, {"approvals": {}}) as data:
        approvals = data.setdefault("approvals", {})
        item = approvals.get(approval_id)
        if not item:
            raise ApprovalRevoked(f"Unknown approval '{approval_id}'.")
        now = int(time.time())
        if item["status"] != "pending":
            raise ApprovalRevoked(f"Approval '{approval_id}' is {item['status']}.")
        if item["expires_at"] <= now:
            item["status"] = "expired"
            raise ApprovalExpired(f"Approval '{approval_id}' expired.")
        item["status"] = to_status
        item["approved_by"] = approver
        item["approved_at"] = now
        return dict(item)


def approve(approval_id: str, approver: str = "local-user") -> dict:
    return _transition(approval_id, approver, "approved")


def deny(approval_id: str, approver: str = "local-user") -> dict:
    return _transition(approval_id, approver, "denied")


def consume(approval_id: str, skill: str, action: str, params: dict,
            actor: str = "local-user") -> dict:
    """Atomically validate and single-use consume an approval.

    The status check and the ``approved → consumed`` write happen inside
    one file-locked critical section, so concurrent processes cannot both
    observe ``approved`` and both execute. Also binds the executing actor:
    the principal consuming the approval must be the one that requested it.
    Raises on any mismatch.
    """
    with localstore.locked_json(_STORE, {"approvals": {}}) as data:
        approvals = data.setdefault("approvals", {})
        item = approvals.get(approval_id)
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
            raise ApprovalExpired(f"Approval '{approval_id}' expired.")
        if item["status"] != "approved":
            raise ApprovalRevoked(f"Approval '{approval_id}' is {item['status']}.")
        # actor binding: only the requesting principal may consume
        if item.get("actor", "local-user") != actor:
            raise ApprovalRevoked(
                f"Approval '{approval_id}' was requested by "
                f"'{item.get('actor')}', not '{actor}'.")
        # parameter binding: the approval covers EXACTLY these params
        if (item["skill"], item["action"]) != (skill, action) or \
                item["params_hash"] != _params_hash(params):
            raise ApprovalRevoked(
                f"Approval '{approval_id}' does not match this skill/action/parameters.")
        item["status"] = "consumed"
        item["consumed_at"] = now
        return dict(item)

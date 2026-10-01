"""Permission model — human-in-the-loop UI over the runtime approval engine.

This skill is the user-facing surface of ``skillhub.approval``: the same
approval objects that gate write actions in ``registry.dispatch`` are
requested, listed, approved and denied here. One system, not two.

Approvals are bound to exact skill/action/parameters, expire after
``ttl_s`` (default 600s), and are single-use.
"""
from __future__ import annotations

from .. import approval as approval_engine
from ..driver import ActionDef
from ..localstore import LOCAL_NOTE

SKILL = "permission-model"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE


async def request_approval(params: dict) -> dict:
    skill = params.get("skill", "")
    action = params["action"]
    # The human approver must see the TRUE risk tier, not whatever label
    # the caller supplied: resolve the registry-canonical risk for known
    # skill/actions. A caller-supplied downgrade ("write" for a destructive
    # action) is ignored here AND would fail closed at consume() time.
    declared = params.get("risk", "write")
    canonical = declared
    try:
        from .. import registry as _registry
        from ..policy import risk_for as _risk_for
        reg = _registry.load_registry()
        entry = reg.get(skill)
        if entry is not None and action in entry.actions:
            canonical = _risk_for(skill, action, entry.actions[action].risk)
    except Exception:
        canonical = declared
    item = approval_engine.request_approval(
        skill=skill,
        action=action,
        params=params.get("params", {}) or {},
        risk=canonical,
        ttl_s=int(params.get("ttl_s", 600)),
    )
    return {"status": "ok", "approval": item,
            "usage": "Approve with permission-model approve, then call the "
                     "target tool with approval_id."}


async def list_pending(params: dict) -> dict:
    return {"status": "ok", "pending": approval_engine.list_pending()}


async def approve(params: dict) -> dict:
    item = approval_engine.approve(params["request_id"])
    return {"status": "ok", "approval": item}


async def deny(params: dict) -> dict:
    item = approval_engine.deny(params["request_id"])
    return {"status": "ok", "approval": item}


ACTIONS = {
    "request_approval": ActionDef(
        "Request approval for a skill action (returns approval_id).",
        {"skill": {"type": "string"},
         "action": {"type": "string"},
         "params": {"type": "object", "default": {}},
         "risk": {"type": "string", "default": "write"},
         "ttl_s": {"type": "integer", "default": 600}},
        ["action"], request_approval, write=True, risk="write",
        output_schema={"type": "object"}),
    "list_pending": ActionDef("List pending approval requests.", {}, [],
                              list_pending),
    "approve": ActionDef("Approve a request by approval_id (needs confirm=true).",
        {"request_id": {"type": "string"}}, ["request_id"], approve,
        write=True, risk="write"),
    "deny": ActionDef("Deny a request by approval_id (needs confirm=true).",
        {"request_id": {"type": "string"}}, ["request_id"], deny,
        write=True, risk="write"),
}

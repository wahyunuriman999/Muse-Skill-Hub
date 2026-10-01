"""Permission model — LOCAL approval-queue reference implementation.

Real approve/deny workflow with a local JSON queue. Reference implementation of
the runtime permission interface — not connected to any production permission
system. Swap the storage backend for production use.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "permission-model"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "permissions"


def _load() -> list:
    return read_json(_STORE, [])


def _save(items: list) -> None:
    write_json(_STORE, items)


async def request_approval(params: dict) -> dict:
    items = _load()
    item = {"id": uuid.uuid4().hex[:8], "action": params["action"],
            "params": params.get("params", {}), "status": "pending",
            "created_at": int(time.time())}
    items.append(item)
    _save(items)
    return {"status": "ok", "request": item}


async def list_pending(params: dict) -> dict:
    items = [i for i in _load() if i["status"] == "pending"]
    return {"status": "ok", "pending": items}


async def approve(params: dict) -> dict:
    items = _load()
    for i in items:
        if i["id"] == params["request_id"]:
            i["status"] = "approved"
            _save(items)
            return {"status": "ok", "request": i}
    raise SkillError(SKILL, "not_found", "No such request.")


async def deny(params: dict) -> dict:
    items = _load()
    for i in items:
        if i["id"] == params["request_id"]:
            i["status"] = "denied"
            _save(items)
            return {"status": "ok", "request": i}
    raise SkillError(SKILL, "not_found", "No such request.")


ACTIONS = {
    "request_approval": ActionDef("Queue a permission request (needs confirm=true).",
        {"action": {"type": "string"}, "params": {"type": "object", "default": {}}},
        ["action"], request_approval, write=True),
    "list_pending": ActionDef("List pending permission requests.", {}, [], list_pending),
    "approve": ActionDef("Approve a request (needs confirm=true).",
        {"request_id": {"type": "string"}}, ["request_id"], approve, write=True),
    "deny": ActionDef("Deny a request (needs confirm=true).",
        {"request_id": {"type": "string"}}, ["request_id"], deny, write=True),
}

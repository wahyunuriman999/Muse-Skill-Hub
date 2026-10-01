"""Wearables comms — LOCAL notification/call outbox reference implementation.

Queues outbound notifications/messages for delivery through a connected
wearable. Real queueing logic with honest delivery semantics: items sit in the
local outbox until a connected wearable's companion app drains them — this
driver never pretends a message was delivered when it was only queued.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "wearables-comms"
REQUIRED_ENV: list[str] = []
SETUP_HELP = (LOCAL_NOTE + " Delivery requires a connected wearable whose companion "
              "app drains the outbox.")

_STORE = "wearables-outbox"


async def queue_notification(params: dict) -> dict:
    items = read_json(_STORE, [])
    item = {"id": uuid.uuid4().hex[:8], "kind": params.get("kind", "notification"),
            "to": params.get("to", ""), "text": params["text"],
            "status": "queued", "queued_at": int(time.time())}
    items.append(item)
    write_json(_STORE, items)
    return {"status": "ok", "queued": item,
            "note": "Queued, NOT delivered — a connected wearable must drain the outbox."}


async def list_outbox(params: dict) -> dict:
    items = read_json(_STORE, [])
    if params.get("status"):
        items = [i for i in items if i["status"] == params["status"]]
    return {"status": "ok", "outbox": items}


ACTIONS = {
    "queue_notification": ActionDef("Queue a notification/message for a wearable (needs confirm=true).",
        {"text": {"type": "string"}, "to": {"type": "string"},
         "kind": {"type": "string", "default": "notification"}},
        ["text"], queue_notification, write=True),
    "list_outbox": ActionDef("List queued/delivered wearable messages.",
        {"status": {"type": "string", "description": "queued|delivered"}},
        [], list_outbox),
}

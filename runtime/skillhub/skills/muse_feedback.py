"""Muse feedback — LOCAL feedback outbox reference implementation.

Queues feedback/feature requests locally as structured records. Reference
implementation of the feedback interface — in production, the agent submits
these to the Muse team through the product's feedback channel; this driver
honestly stores them in the local outbox instead of pretending to transmit.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "muse-feedback"
REQUIRED_ENV: list[str] = []
SETUP_HELP = (LOCAL_NOTE + " In production these records are submitted to the "
              "Muse team through the product feedback channel.")

_STORE = "feedback-outbox"


async def submit_feedback(params: dict) -> dict:
    items = read_json(_STORE, [])
    item = {"id": uuid.uuid4().hex[:8], "category": params.get("category", "general"),
            "text": params["text"], "queued_at": int(time.time()),
            "transmitted": False}
    items.append(item)
    write_json(_STORE, items)
    return {"status": "ok", "queued": item,
            "note": "Stored in the local outbox; wire the production feedback channel to transmit."}


async def list_feedback(params: dict) -> dict:
    return {"status": "ok", "outbox": read_json(_STORE, [])}


ACTIONS = {
    "submit_feedback": ActionDef("Queue a feedback item (needs confirm=true).",
        {"text": {"type": "string"}, "category": {"type": "string", "default": "general"}},
        ["text"], submit_feedback, write=True),
    "list_feedback": ActionDef("List queued feedback.", {}, [], list_feedback),
}

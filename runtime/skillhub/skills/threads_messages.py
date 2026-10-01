"""Threads messages driver — real Threads API conversation endpoints.

Note: the Threads API has no DM inbox endpoints. This driver exposes what the
API does support: replies on a thread and the reply conversation around it.
Set THREADS_ACCESS_TOKEN (shared with the meta-threads driver).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "threads-messages"
REQUIRED_ENV = ["THREADS_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, add the Threads use case, "
    "authorize with threads_basic, and set THREADS_ACCESS_TOKEN. "
    "Note: the Threads API exposes replies/conversations, not a DM inbox."
)

_BASE = "https://graph.threads.net/v1.0"


def _token() -> str:
    token = cred("THREADS_ACCESS_TOKEN", SKILL)
    return token


async def list_replies(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['thread_id']}/replies",
                          params={"fields": "id,text,username,timestamp,like_count",
                                  "access_token": _token()})
    return {"status": "ok", "replies": r.get("data", [])}


async def get_conversation(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['thread_id']}/conversation",
                          params={"fields": "id,text,username,timestamp",
                                  "access_token": _token()})
    return {"status": "ok", "conversation": r.get("data", [])}


ACTIONS = {
    "list_replies": ActionDef("List replies on one of your threads.",
        {"thread_id": {"type": "string", "description": "Threads post ID"}},
        ["thread_id"], list_replies),
    "get_conversation": ActionDef("Get the reply conversation around a thread.",
        {"thread_id": {"type": "string"}},
        ["thread_id"], get_conversation),
}

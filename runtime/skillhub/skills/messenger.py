"""Messenger driver — real Messenger Platform API (via Meta Graph API).

Setup: a Page access token with pages_messaging permission. Create a Meta app,
connect a Facebook Page, subscribe it to messaging. Set MESSENGER_PAGE_TOKEN
(or reuse FACEBOOK_ACCESS_TOKEN if it has the scope).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "messenger"
REQUIRED_ENV = ["MESSENGER_PAGE_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, connect a Facebook Page, "
    "grant pages_messaging, copy the Page access token, and set MESSENGER_PAGE_TOKEN."
)

_BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    token = os.environ.get("MESSENGER_PAGE_TOKEN") or os.environ.get("FACEBOOK_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def list_conversations(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/conversations",
                          params={"fields": "participants,snippet,updated_time",
                                  "limit": min(int(params.get("limit", 20)), 50),
                                  "access_token": _token()})
    return {"status": "ok", "conversations": r.get("data", [])}


async def send_message(params: dict) -> dict:
    import json
    r = await api_request(SKILL, "POST", f"{_BASE}/me/messages",
                          params={"recipient": json.dumps({"id": params["recipient_id"]}),
                                  "message": json.dumps({"text": params["text"]}),
                                  "access_token": _token()})
    return {"status": "ok", "message_id": r.get("message_id")}


ACTIONS = {
    "list_conversations": ActionDef("List Messenger conversations.",
        {"limit": {"type": "integer", "default": 20, "maximum": 50}},
        [], list_conversations),
    "send_message": ActionDef("Send a Messenger message (needs confirm=true).",
        {"recipient_id": {"type": "string"}, "text": {"type": "string"}},
        ["recipient_id", "text"], send_message, write=True),
}

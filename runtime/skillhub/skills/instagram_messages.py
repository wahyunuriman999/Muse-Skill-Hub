"""Instagram messages driver — real Instagram Messaging API (via Meta Graph API).

Setup: an Instagram business/creator account linked to a Facebook Page, with a
Page access token granted instagram_manage_messages. Set INSTAGRAM_PAGE_TOKEN
(or reuse FACEBOOK_ACCESS_TOKEN if it has the scope).
"""
from __future__ import annotations

import json
import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "instagram-messages"
REQUIRED_ENV = ["INSTAGRAM_PAGE_TOKEN"]
SETUP_HELP = (
    "Link your Instagram business account to a Facebook Page, grant "
    "instagram_manage_messages on your Meta app token, and set INSTAGRAM_PAGE_TOKEN."
)

_BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    token = os.environ.get("INSTAGRAM_PAGE_TOKEN") or os.environ.get("FACEBOOK_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def list_conversations(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/conversations",
                          params={"platform": "instagram",
                                  "fields": "participants,snippet,updated_time",
                                  "limit": min(int(params.get("limit", 20)), 50),
                                  "access_token": _token()})
    return {"status": "ok", "conversations": r.get("data", [])}


async def send_message(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/me/messages",
                          params={"recipient": json.dumps({"id": params["recipient_id"]}),
                                  "message": json.dumps({"text": params["text"]}),
                                  "access_token": _token()})
    return {"status": "ok", "message_id": r.get("message_id")}


ACTIONS = {
    "list_conversations": ActionDef("List Instagram message conversations.",
        {"limit": {"type": "integer", "default": 20, "maximum": 50}},
        [], list_conversations),
    "send_message": ActionDef("Send an Instagram DM (needs confirm=true).",
        {"recipient_id": {"type": "string"}, "text": {"type": "string"}},
        ["recipient_id", "text"], send_message, write=True),
}

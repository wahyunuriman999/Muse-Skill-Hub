"""Gmail driver — real Gmail REST API implementation.

Setup: an OAuth2 access token with Gmail scopes (gmail.readonly, gmail.send).
Get one via the Google OAuth Playground:
https://developers.google.com/oauthplayground (select Gmail API scopes),
or mint one from your own OAuth client. Set GOOGLE_OAUTH_TOKEN.
"""
from __future__ import annotations

import base64
import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "gmail"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Gmail API scopes "
    "(gmail.readonly, gmail.send), authorize, and set the access token as GOOGLE_OAUTH_TOKEN. "
    "Tokens expire; refresh with your own OAuth client for long-term use."
)

_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _headers() -> dict:
    token = os.environ.get("GOOGLE_OAUTH_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}"}


async def list_messages(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/messages", headers=_headers(),
                          params={"q": params.get("query", ""),
                                  "maxResults": min(int(params.get("limit", 10)), 50)})
    return {"status": "ok", "messages": [
        {"id": m["id"], "threadId": m.get("threadId")} for m in r.get("messages", [])]}


async def get_message(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/messages/{params['message_id']}",
                          headers=_headers(),
                          params={"format": "metadata",
                                  "metadataHeaders": ["From", "To", "Subject", "Date"]})
    headers = {h["name"]: h.get("value") for h in r.get("payload", {}).get("headers", [])}
    return {"status": "ok", "id": r.get("id"), "snippet": r.get("snippet"),
            "headers": headers}


async def send_message(params: dict) -> dict:
    raw_text = (f"To: {params['to']}\r\n"
                f"Subject: {params['subject']}\r\n"
                f"\r\n{params['body']}")
    raw = base64.urlsafe_b64encode(raw_text.encode("utf-8")).decode("ascii")
    r = await api_request(SKILL, "POST", f"{_BASE}/messages/send", headers=_headers(),
                          json={"raw": raw})
    return {"status": "ok", "id": r.get("id"), "threadId": r.get("threadId")}


ACTIONS = {
    "list_messages": ActionDef("Search/list messages in the inbox.",
        {"query": {"type": "string", "default": "",
                   "description": "Gmail search query, e.g. 'from:boss subject:report newer_than:7d'"},
         "limit": {"type": "integer", "default": 10, "maximum": 50}},
        [], list_messages),
    "get_message": ActionDef("Get a message's headers and snippet.",
        {"message_id": {"type": "string", "description": "Gmail message ID"}},
        ["message_id"], get_message),
    "send_message": ActionDef("Send an email (needs confirm=true).",
        {"to": {"type": "string"}, "subject": {"type": "string"},
         "body": {"type": "string"}},
        ["to", "subject", "body"], send_message, write=True),
}

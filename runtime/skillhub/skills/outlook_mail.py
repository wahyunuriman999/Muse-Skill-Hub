"""Outlook Mail driver — real Microsoft Graph implementation.

Setup: an OAuth2 access token with Mail.ReadWrite and Mail.Send. Register an app
at https://portal.azure.com (Microsoft Entra) or mint a token in the Graph
Explorer for testing. Set MICROSOFT_ACCESS_TOKEN (shared with outlook-calendar/contacts).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "outlook-mail"
REQUIRED_ENV = ["MICROSOFT_ACCESS_TOKEN"]
SETUP_HELP = (
    "Register an app at https://portal.azure.com with Mail.ReadWrite and Mail.Send "
    "(delegated), complete OAuth, and set MICROSOFT_ACCESS_TOKEN. For quick testing, "
    "mint one in https://developer.microsoft.com/graph/graph-explorer."
)

_BASE = "https://graph.microsoft.com/v1.0/me"


def _headers() -> dict:
    token = cred("MICROSOFT_ACCESS_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(m: dict) -> dict:
    return {"id": m.get("id"), "subject": m.get("subject"),
            "from": ((m.get("from") or {}).get("emailAddress") or {}).get("address"),
            "received": m.get("receivedDateTime"),
            "preview": m.get("bodyPreview")}


async def list_messages(params: dict) -> dict:
    q = {"$top": min(int(params.get("limit", 20)), 100),
         "$orderby": "receivedDateTime desc",
         "$select": "id,subject,from,receivedDateTime,bodyPreview"}
    if params.get("query"):
        q["$search"] = f'"{params["query"]}"'
    r = await api_request(SKILL, "GET", f"{_BASE}/messages",
                          headers=_headers(), params=q)
    return {"status": "ok", "messages": [_fmt(m) for m in r.get("value", [])]}


async def send_mail(params: dict) -> dict:
    body = {"message": {"subject": params["subject"],
                        "body": {"contentType": "Text", "content": params["body"]},
                        "toRecipients": [{"emailAddress": {"address": params["to"]}}]}}
    await api_request(SKILL, "POST", f"{_BASE}/sendMail",
                      headers=_headers(), json=body)
    return {"status": "ok", "sent_to": params["to"]}


ACTIONS = {
    "list_messages": ActionDef("List/search mailbox messages.",
        {"query": {"type": "string", "description": "Search keywords"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_messages, required_scopes=["Mail.Read"]),
    "send_mail": ActionDef("Send an email (needs confirm=true).",
        {"to": {"type": "string"}, "subject": {"type": "string"},
         "body": {"type": "string"}},
        ["to", "subject", "body"], send_mail, write=True, required_scopes=["Mail.Send"]),
}

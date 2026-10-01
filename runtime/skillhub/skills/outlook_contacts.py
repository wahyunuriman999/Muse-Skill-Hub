"""Outlook Contacts driver — real Microsoft Graph implementation.

Setup: an OAuth2 access token with Contacts.ReadWrite. Set MICROSOFT_ACCESS_TOKEN
(shared with outlook-calendar/mail).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "outlook-contacts"
REQUIRED_ENV = ["MICROSOFT_ACCESS_TOKEN"]
SETUP_HELP = (
    "Register an app at https://portal.azure.com with Contacts.ReadWrite (delegated), "
    "complete OAuth, and set MICROSOFT_ACCESS_TOKEN."
)

_BASE = "https://graph.microsoft.com/v1.0/me/contacts"


def _headers() -> dict:
    token = cred("MICROSOFT_ACCESS_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(c: dict) -> dict:
    emails = [e.get("address") for e in c.get("emailAddresses", [])]
    return {"id": c.get("id"), "name": c.get("displayName"), "emails": emails}


async def list_contacts(params: dict) -> dict:
    q = {"$top": min(int(params.get("limit", 20)), 100)}
    if params.get("query"):
        q["$search"] = f'"{params["query"]}"'
    r = await api_request(SKILL, "GET", _BASE, headers=_headers(), params=q)
    return {"status": "ok", "contacts": [_fmt(c) for c in r.get("value", [])]}


async def create_contact(params: dict) -> dict:
    body = {"givenName": params.get("given_name"), "surname": params.get("surname"),
            "displayName": params.get("display_name")}
    if params.get("email"):
        body["emailAddresses"] = [{"address": params["email"]}]
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(), json=body)
    return {"status": "ok", "contact": _fmt(r)}


ACTIONS = {
    "list_contacts": ActionDef("List/search Outlook contacts.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_contacts, required_scopes=["Contacts.Read"]),
    "create_contact": ActionDef("Create a contact (needs confirm=true).",
        {"given_name": {"type": "string"}, "surname": {"type": "string"},
         "display_name": {"type": "string"}, "email": {"type": "string"}},
        [], create_contact, write=True, required_scopes=["Contacts.ReadWrite"]),
}

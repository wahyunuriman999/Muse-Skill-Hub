"""GoHighLevel driver — real HighLevel API v2 implementation.

Setup: a Private Integration API key from your GoHighLevel sub-account
(Settings → Private Integrations). Set GHL_API_KEY.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "ghl"
REQUIRED_ENV = ["GHL_API_KEY"]
SETUP_HELP = (
    "In GoHighLevel, go to Settings → Private Integrations, create an integration "
    "with contacts scope, copy the API key, and set GHL_API_KEY."
)

_BASE = "https://services.leadconnectorhq.com"


def _headers() -> dict:
    key = cred("GHL_API_KEY", SKILL)
    return {"Authorization": f"Bearer {key}", "Version": "2021-07-28",
            "Content-Type": "application/json"}


def _fmt(c: dict) -> dict:
    return {"id": c.get("id"), "name": c.get("contactName"),
            "email": c.get("email"), "phone": c.get("phone"),
            "tags": c.get("tags")}


async def list_contacts(params: dict) -> dict:
    q = {"limit": min(int(params.get("limit", 20)), 100)}
    if params.get("query"):
        q["query"] = params["query"]
    r = await api_request(SKILL, "GET", f"{_BASE}/contacts/",
                          headers=_headers(), params=q)
    return {"status": "ok", "contacts": [_fmt(c) for c in r.get("contacts", [])]}


async def get_contact(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/contacts/{params['contact_id']}",
                          headers=_headers())
    return {"status": "ok", "contact": _fmt(r.get("contact", {}))}


async def create_contact(params: dict) -> dict:
    body = {k: params[k] for k in ("firstName", "lastName", "email", "phone")
            if params.get(k)}
    if params.get("location_id"):
        q = {"locationId": params["location_id"]}
    else:
        q = None
    r = await api_request(SKILL, "POST", f"{_BASE}/contacts/",
                          headers=_headers(), params=q, json=body)
    return {"status": "ok", "contact": _fmt(r.get("contact", {}))}


ACTIONS = {
    "list_contacts": ActionDef("List/search contacts.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_contacts),
    "get_contact": ActionDef("Get one contact's details.",
        {"contact_id": {"type": "string"}}, ["contact_id"], get_contact),
    "create_contact": ActionDef("Create a contact (needs confirm=true).",
        {"firstName": {"type": "string"}, "lastName": {"type": "string"},
         "email": {"type": "string"}, "phone": {"type": "string"},
         "location_id": {"type": "string"}},
        [], create_contact, write=True),
}

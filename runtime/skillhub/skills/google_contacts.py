"""Google Contacts driver — real People API implementation.

Setup: an OAuth2 access token with contacts scopes.
Set GOOGLE_OAUTH_TOKEN (shared with the other Google drivers).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "google-contacts"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select People API scopes "
    "(contacts), authorize, and set GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://people.googleapis.com/v1"


def _headers() -> dict:
    token = os.environ.get("GOOGLE_OAUTH_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(p: dict) -> dict:
    names = [n.get("displayName") for n in p.get("names", [])]
    emails = [e.get("value") for e in p.get("emailAddresses", [])]
    return {"resourceName": p.get("resourceName"), "names": names, "emails": emails}


async def list_contacts(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/people/me/connections",
                          headers=_headers(),
                          params={"personFields": "names,emailAddresses",
                                  "pageSize": min(int(params.get("limit", 50)), 200)})
    return {"status": "ok", "contacts": [_fmt(p) for p in r.get("connections", [])]}


async def create_contact(params: dict) -> dict:
    body = {"names": [{"givenName": params.get("given_name"),
                       "familyName": params.get("family_name")}]}
    if params.get("email"):
        body["emailAddresses"] = [{"value": params["email"]}]
    r = await api_request(SKILL, "POST", f"{_BASE}/people:createContact",
                          headers=_headers(), json=body)
    return {"status": "ok", "contact": _fmt(r)}


ACTIONS = {
    "list_contacts": ActionDef("List Google contacts.",
        {"limit": {"type": "integer", "default": 50, "maximum": 200}},
        [], list_contacts),
    "create_contact": ActionDef("Create a contact (needs confirm=true).",
        {"given_name": {"type": "string"}, "family_name": {"type": "string"},
         "email": {"type": "string"}},
        [], create_contact, write=True),
}

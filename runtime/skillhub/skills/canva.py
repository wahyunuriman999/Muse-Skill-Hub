"""Canva driver — real Canva Connect API implementation.

Setup: an OAuth access token with design scopes (design:content:read etc.).
Create an integration at https://www.canva.com/developers and complete OAuth.
Set CANVA_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "canva"
REQUIRED_ENV = ["CANVA_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create an integration at https://www.canva.com/developers, complete the OAuth "
    "flow with design scopes, and set CANVA_ACCESS_TOKEN."
)

_BASE = "https://api.canva.com/rest/v1"


def _headers() -> dict:
    token = os.environ.get("CANVA_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}"}


async def list_designs(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/designs", headers=_headers(),
                          params={"page_size": min(int(params.get("limit", 20)), 100)})
    return {"status": "ok", "designs": [
        {"id": d.get("id"), "title": d.get("title"), "url": d.get("urls", {}).get("view_url"),
         "created_at": d.get("created_at")}
        for d in r.get("items", [])]}


async def get_design(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/designs/{params['design_id']}",
                          headers=_headers())
    return {"status": "ok", "design": {"id": r.get("id"), "title": r.get("title"),
                                       "url": (r.get("urls") or {}).get("view_url")}}


ACTIONS = {
    "list_designs": ActionDef("List the user's Canva designs.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_designs),
    "get_design": ActionDef("Get one design's details.",
        {"design_id": {"type": "string"}}, ["design_id"], get_design),
}

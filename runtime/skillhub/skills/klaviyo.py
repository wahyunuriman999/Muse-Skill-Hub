"""Klaviyo driver — real Klaviyo API implementation.

Setup: a Private API Key from Klaviyo → Settings → API keys.
Set KLAVIYO_API_KEY.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "klaviyo"
REQUIRED_ENV = ["KLAVIYO_API_KEY"]
SETUP_HELP = (
    "In Klaviyo, go to Settings → API keys, create a Private API Key, "
    "and set KLAVIYO_API_KEY."
)

_BASE = "https://a.klaviyo.com/api"


def _headers() -> dict:
    key = cred("KLAVIYO_API_KEY", SKILL)
    return {"Authorization": f"Klaviyo-API-Key {key}",
            "revision": "2024-10-15", "Content-Type": "application/json"}


async def list_lists(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/lists/", headers=_headers(),
                          params={"page[size]": min(int(params.get("limit", 20)), 100)})
    return {"status": "ok", "lists": [
        {"id": l.get("id"), "name": (l.get("attributes") or {}).get("name")}
        for l in r.get("data", [])]}


async def list_campaigns(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/campaigns/", headers=_headers(),
                          params={"page[size]": min(int(params.get("limit", 20)), 100)})
    return {"status": "ok", "campaigns": [
        {"id": c.get("id"), "name": (c.get("attributes") or {}).get("name"),
         "status": (c.get("attributes") or {}).get("status")}
        for c in r.get("data", [])]}


ACTIONS = {
    "list_lists": ActionDef("List Klaviyo lists.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_lists),
    "list_campaigns": ActionDef("List Klaviyo campaigns.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_campaigns),
}

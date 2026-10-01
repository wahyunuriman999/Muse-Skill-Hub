"""Calendly driver — real Calendly API v2 implementation.

Setup: a Personal Access Token from https://calendly.com/integrations/api_webhooks.
Set CALENDLY_API_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "calendly"
REQUIRED_ENV = ["CALENDLY_API_TOKEN"]
SETUP_HELP = (
    "Go to https://calendly.com/integrations/api_webhooks, create a Personal "
    "Access Token, and set CALENDLY_API_TOKEN."
)

_BASE = "https://api.calendly.com"


def _headers() -> dict:
    token = os.environ.get("CALENDLY_API_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _me() -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/users/me", headers=_headers())
    return r["resource"]


async def list_event_types(params: dict) -> dict:
    me = await _me()
    r = await api_request(SKILL, "GET", f"{_BASE}/event_types", headers=_headers(),
                          params={"user": me["uri"],
                                  "count": min(int(params.get("limit", 20)), 100)})
    return {"status": "ok", "event_types": [
        {"uri": e["uri"], "name": e.get("name"), "slug": e.get("slug"),
         "scheduling_url": e.get("scheduling_url"), "active": e.get("active")}
        for e in r.get("collection", [])]}


async def list_events(params: dict) -> dict:
    me = await _me()
    q = {"user": me["uri"], "count": min(int(params.get("limit", 20)), 100),
         "sort": "start_time:asc"}
    if params.get("min_start_time"):
        q["min_start_time"] = params["min_start_time"]
    r = await api_request(SKILL, "GET", f"{_BASE}/scheduled_events",
                          headers=_headers(), params=q)
    return {"status": "ok", "events": [
        {"uri": e["uri"], "name": e.get("name"), "start_time": e.get("start_time"),
         "end_time": e.get("end_time"), "status": e.get("status")}
        for e in r.get("collection", [])]}


ACTIONS = {
    "list_event_types": ActionDef("List the user's Calendly event types.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_event_types),
    "list_events": ActionDef("List scheduled events.",
        {"min_start_time": {"type": "string", "description": "ISO8601 lower bound"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_events),
}

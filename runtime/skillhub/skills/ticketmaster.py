"""Ticketmaster driver — real Ticketmaster Discovery API implementation.

Setup: a free API key from https://developer.ticketmaster.com (create an app,
copy the Consumer Key). Set TICKETMASTER_API_KEY.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "ticketmaster"
REQUIRED_ENV = ["TICKETMASTER_API_KEY"]
SETUP_HELP = (
    "Sign up at https://developer.ticketmaster.com, create an app, and copy the "
    "Consumer Key. Set it as TICKETMASTER_API_KEY."
)

_BASE = "https://app.ticketmaster.com/discovery/v2/events.json"


def _key() -> str:
    key = os.environ.get("TICKETMASTER_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return key


def _fmt(e: dict) -> dict:
    venue = (e.get("_embedded") or {}).get("venues", [{}])[0]
    return {"id": e.get("id"), "name": e.get("name"),
            "date": (e.get("dates") or {}).get("start", {}).get("localDate"),
            "venue": venue.get("name"), "city": venue.get("city", {}).get("name"),
            "url": e.get("url")}


async def search_events(params: dict) -> dict:
    q = {"apikey": _key(), "size": min(int(params.get("limit", 10)), 50)}
    for k in ("keyword", "city", "countryCode", "classificationName"):
        if params.get(k):
            q[k] = params[k]
    r = await api_request(SKILL, "GET", _BASE, params=q)
    events = ((r.get("_embedded") or {}).get("events")) or []
    return {"status": "ok", "events": [_fmt(e) for e in events],
            "total": (r.get("page") or {}).get("totalElements")}


ACTIONS = {
    "search_events": ActionDef("Search concerts, sports, arts and theater events.",
        {"keyword": {"type": "string", "description": "e.g. 'Coldplay', 'jazz'"},
         "city": {"type": "string"}, "countryCode": {"type": "string", "description": "e.g. ID, US"},
         "classificationName": {"type": "string", "description": "music, sports, arts"},
         "limit": {"type": "integer", "default": 10, "maximum": 50}},
        [], search_events),
}

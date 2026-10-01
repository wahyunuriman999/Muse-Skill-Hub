"""OpenTable driver — prefilled search/reservation links + availability notes.

OpenTable offers no public booking API, so this driver builds the same deep
links OpenTable's own site uses (prefilled restaurant search and reservation
widget URLs) instead of pretending to book through a nonexistent endpoint.
"""
from __future__ import annotations

import urllib.parse

from ..driver import ActionDef

SKILL = "opentable"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No credentials needed — builds OpenTable deep links."

WHY = "OpenTable has no public booking API; complete the reservation on opentable.com."


async def search_restaurants(params: dict) -> dict:
    q = urllib.parse.urlencode({"term": params.get("query", ""),
                                "covers": params.get("covers", 2)})
    return {"status": "ok", "url": f"https://www.opentable.com/s?{q}", "why": WHY}


async def reservation_link(params: dict) -> dict:
    q = urllib.parse.urlencode({"covers": params.get("covers", 2),
                                "dateTime": params.get("datetime", "")})
    return {"status": "ok",
            "url": f"https://www.opentable.com/r/{params['restaurant_slug']}?{q}",
            "why": WHY}


ACTIONS = {
    "search_restaurants": ActionDef("Build a prefilled OpenTable restaurant search link.",
        {"query": {"type": "string"}, "covers": {"type": "integer", "default": 2}},
        [], search_restaurants),
    "reservation_link": ActionDef("Build a prefilled reservation link for a restaurant.",
        {"restaurant_slug": {"type": "string",
                             "description": "Slug from the restaurant's OpenTable URL"},
         "covers": {"type": "integer", "default": 2},
         "datetime": {"type": "string", "description": "ISO8601"}},
        ["restaurant_slug"], reservation_link),
}

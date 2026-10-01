"""Places search driver — real Google Places API (new) implementation.

Setup: Google Cloud Console > enable Places API > create API key with Places scope.
Set GOOGLE_MAPS_API_KEY.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "places-search"
REQUIRED_ENV = ["GOOGLE_MAPS_API_KEY"]
SETUP_HELP = ("Google Cloud Console > APIs & Services > enable 'Places API (New)' > "
              "Credentials > Create API key, restrict it to Places API.")

_BASE = "https://places.googleapis.com/v1/places"


def _headers() -> dict:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"X-Goog-Api-Key": key, "Content-Type": "application/json",
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.id"}


async def search_places(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}:searchText", headers=_headers(),
                          json={"textQuery": params["query"], "maxResultCount": 8})
    return {"status": "ok", "places": [
        {"name": (p.get("displayName") or {}).get("text"),
         "address": p.get("formattedAddress"), "rating": p.get("rating")}
        for p in r.get("places", [])]}


ACTIONS = {
    "search_places": ActionDef("Search for places (restaurants, cafes, etc.).",
        {"query": {"type": "string", "description": "e.g. 'coffee shop Jakarta Selatan'"}},
        ["query"], search_places),
}

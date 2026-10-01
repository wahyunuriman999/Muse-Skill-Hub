"""Booking router driver — routes booking intents to real drivers.

Flights → the duffel driver (needs DUFFEL_ACCESS_TOKEN).
Event tickets → the ticketmaster driver (needs TICKETMASTER_API_KEY).
Hotels/restaurants → deep links to Booking.com / OpenTable search pages
(these providers offer no public booking API; the links open prefilled searches).
"""
from __future__ import annotations

import urllib.parse

from ..driver import ActionDef
from ..errors import SkillError

SKILL = "booking"
REQUIRED_ENV: list[str] = []
SETUP_HELP = (
    "Set DUFFEL_ACCESS_TOKEN for flight search/booking and TICKETMASTER_API_KEY "
    "for event tickets. Hotels and restaurants return prefilled search links."
)


async def _delegate(skill: str, action: str, params: dict) -> dict:
    from ..registry import load_registry, dispatch
    entry = load_registry().get(skill)
    if entry is None or not entry.implemented:
        raise SkillError(SKILL, "dependency_missing",
                         f"The '{skill}' driver is not available.")
    return await dispatch(entry, action, params, confirm=False)


async def search_flights(params: dict) -> dict:
    return await _delegate("duffel", "search_offers", {
        "origin": params["origin"], "destination": params["destination"],
        "departure_date": params["departure_date"],
        "limit": params.get("limit", 5)})


async def search_events(params: dict) -> dict:
    return await _delegate("ticketmaster", "search_events", {
        "keyword": params.get("keyword", ""),
        "city": params.get("city", ""), "limit": params.get("limit", 10)})


async def hotel_search_link(params: dict) -> dict:
    q = urllib.parse.urlencode({
        "ss": params["destination"],
        "checkin": params.get("checkin", ""), "checkout": params.get("checkout", ""),
        "group_adults": params.get("adults", 2)})
    return {"status": "ok",
            "url": f"https://www.booking.com/searchresults.html?{q}",
            "note": "Booking.com has no public booking API; this opens a prefilled search."}


async def restaurant_search_link(params: dict) -> dict:
    q = urllib.parse.urlencode({"term": params.get("restaurant", ""),
                                "covers": params.get("covers", 2),
                                "dateTime": params.get("datetime", "")})
    return {"status": "ok",
            "url": f"https://www.opentable.com/s?{q}",
            "note": "OpenTable has no public booking API; this opens a prefilled search."}


ACTIONS = {
    "search_flights": ActionDef("Search flights via the duffel driver.",
        {"origin": {"type": "string"}, "destination": {"type": "string"},
         "departure_date": {"type": "string"},
         "limit": {"type": "integer", "default": 5}},
        ["origin", "destination", "departure_date"], search_flights),
    "search_events": ActionDef("Search event tickets via the ticketmaster driver.",
        {"keyword": {"type": "string"}, "city": {"type": "string"},
         "limit": {"type": "integer", "default": 10}},
        [], search_events),
    "hotel_search_link": ActionDef("Build a prefilled Booking.com hotel search link.",
        {"destination": {"type": "string"}, "checkin": {"type": "string"},
         "checkout": {"type": "string"}, "adults": {"type": "integer", "default": 2}},
        ["destination"], hotel_search_link),
    "restaurant_search_link": ActionDef("Build a prefilled OpenTable search link.",
        {"restaurant": {"type": "string"}, "covers": {"type": "integer", "default": 2},
         "datetime": {"type": "string", "description": "ISO8601"}},
        [], restaurant_search_link),
}

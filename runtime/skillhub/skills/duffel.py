"""Duffel driver — real Duffel API implementation (flights).

Setup: an API key from https://app.duffel.com (test keys work in test mode).
Set DUFFEL_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "duffel"
REQUIRED_ENV = ["DUFFEL_ACCESS_TOKEN"]
SETUP_HELP = (
    "Sign up at https://app.duffel.com, copy an API key (test keys work for "
    "searching), and set DUFFEL_ACCESS_TOKEN."
)

_BASE = "https://api.duffel.com"


def _headers() -> dict:
    token = os.environ.get("DUFFEL_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Duffel-Version": "v2",
            "Content-Type": "application/json"}


async def search_offers(params: dict) -> dict:
    body = {"data": {
        "slices": [{"origin": params["origin"], "destination": params["destination"],
                    "departure_date": params["departure_date"]}],
        "passengers": [{"age": int(params.get("passenger_age", 30))}],
        "max_connections": int(params.get("max_connections", 1))}}
    r = await api_request(SKILL, "POST", f"{_BASE}/air/offer_requests",
                          headers=_headers(),
                          params={"limit": min(int(params.get("limit", 5)), 20)},
                          json=body)
    offers = r.get("data", {}).get("offers", [])
    return {"status": "ok", "offers": [
        {"id": o.get("id"), "total_amount": o.get("total_amount"),
         "total_currency": o.get("total_currency"),
         "airline": (o.get("owner") or {}).get("name"),
         "slices": [{"origin": s.get("origin", {}).get("iata_code"),
                     "destination": s.get("destination", {}).get("iata_code"),
                     "departing": s.get("departing_at")}
                    for s in o.get("slices", [])]}
        for o in offers]}


async def create_order(params: dict) -> dict:
    body = {"data": {"selected_offers": [params["offer_id"]],
                     "payments": [{"type": "balance",
                                   "currency": params["currency"],
                                   "amount": params["amount"]}]}}
    if params.get("passenger"):
        body["data"]["passengers"] = [params["passenger"]]
    r = await api_request(SKILL, "POST", f"{_BASE}/air/orders",
                          headers=_headers(), json=body)
    d = r.get("data", {})
    return {"status": "ok", "order_id": d.get("id"),
            "booking_reference": d.get("booking_reference"),
            "total": f"{d.get('total_amount')} {d.get('total_currency')}"}


ACTIONS = {
    "search_offers": ActionDef("Search flight offers (origin/destination are IATA codes).",
        {"origin": {"type": "string", "description": "e.g. CGK"},
         "destination": {"type": "string", "description": "e.g. SIN"},
         "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
         "passenger_age": {"type": "integer", "default": 30},
         "max_connections": {"type": "integer", "default": 1},
         "limit": {"type": "integer", "default": 5, "maximum": 20}},
        ["origin", "destination", "departure_date"], search_offers),
    "create_order": ActionDef("Book a selected offer — real money (needs confirm=true).",
        {"offer_id": {"type": "string"}, "currency": {"type": "string"},
         "amount": {"type": "string"},
         "passenger": {"type": "object",
                       "description": "Duffel passenger object (given_name, family_name, ...)"}},
        ["offer_id", "currency", "amount"], create_order, write=True),
}

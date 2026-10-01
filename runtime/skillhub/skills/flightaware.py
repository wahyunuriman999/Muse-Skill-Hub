"""FlightAware driver — real FlightAware AeroAPI implementation.

Setup: an AeroAPI key from https://www.flightaware.com/aeroapi (personal plans available).
AeroAPI uses HTTP Basic auth with the API key as the username. Set FLIGHTAWARE_API_KEY.
"""
from __future__ import annotations

import base64

from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "flightaware"
REQUIRED_ENV = ["FLIGHTAWARE_API_KEY"]
SETUP_HELP = (
    "Sign up at https://www.flightaware.com/aeroapi, get an AeroAPI key, "
    "and set FLIGHTAWARE_API_KEY."
)

_BASE = "https://flightaware.com/aeroapi"


def _headers() -> dict:
    key = cred("FLIGHTAWARE_API_KEY", SKILL)
    basic = base64.b64encode(f"{key}:".encode()).decode()
    return {"Authorization": f"Basic {basic}"}


def _fmt(f: dict) -> dict:
    return {"ident": f.get("ident"), "status": f.get("status"),
            "origin": (f.get("origin") or {}).get("code"),
            "destination": (f.get("destination") or {}).get("code"),
            "departure": f.get("scheduled_out"), "arrival": f.get("scheduled_in"),
            "aircraft": f.get("aircraft_type")}


async def flight_status(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/flights/{params['ident']}",
                          headers=_headers(),
                          params={"max_pages": 1})
    flights = r.get("flights", [])
    return {"status": "ok", "flights": [_fmt(f) for f in flights[:5]]}


ACTIONS = {
    "flight_status": ActionDef("Get live status for a flight ident, e.g. 'GA820' or 'QZ753'.",
        {"ident": {"type": "string", "description": "Airline code + flight number"}},
        ["ident"], flight_status),
}

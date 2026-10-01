"""Tessie driver — real Tessie API implementation (Tesla vehicles).

Setup: an API token from https://dash.tessie.com (Tessie account).
Set TESSIE_API_TOKEN and optionally TESSIE_VIN (default vehicle).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request
from ..credentials import cred, maybe_cred

SKILL = "tessie"
REQUIRED_ENV = ["TESSIE_API_TOKEN"]
SETUP_HELP = (
    "Sign up at https://dash.tessie.com, generate an API token, and set "
    "TESSIE_API_TOKEN. Set TESSIE_VIN to target a specific vehicle."
)

_BASE = "https://api.tessie.com"


def _headers() -> dict:
    token = cred("TESSIE_API_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}"}


def _vin(params: dict) -> str:
    vin = params.get("vin") or maybe_cred("TESSIE_VIN", SKILL)
    if not vin:
        raise CredentialsMissing(SKILL, ["TESSIE_VIN"],
                                 "Pass vin or set TESSIE_VIN.")
    return vin


async def list_vehicles(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/vehicles", headers=_headers())
    items = r.get("results", []) if isinstance(r, dict) else []
    return {"status": "ok", "vehicles": [
        {"vin": v.get("vin"), "display_name": v.get("display_name")}
        for v in items]}


async def get_state(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{_vin(params)}/state",
                          headers=_headers(),
                          params={"fields": "all"})
    return {"status": "ok", "state": {
        "battery_level": r.get("battery_level"),
        "battery_range": r.get("battery_range"),
        "charging_state": r.get("charging_state"),
        "odometer": r.get("odometer"),
        "locked": r.get("locked"),
        "latitude": r.get("latitude"), "longitude": r.get("longitude")}}


ACTIONS = {
    "list_vehicles": ActionDef("List Tessie vehicles on the account.",
        {}, [], list_vehicles),
    "get_state": ActionDef("Read a vehicle's live state (battery, location, locks).",
        {"vin": {"type": "string"}}, [], get_state),
}

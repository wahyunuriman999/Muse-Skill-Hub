"""Withings driver — real Withings API implementation.

Setup: an OAuth2 access token with user.metrics scope. Create an app at
https://developer.withings.com and complete OAuth. Set WITHINGS_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "withings"
REQUIRED_ENV = ["WITHINGS_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create an app at https://developer.withings.com, complete OAuth2 with "
    "user.metrics scope, and set WITHINGS_ACCESS_TOKEN."
)

_BASE = "https://wbsapi.withings.net"

# measure type ids: 1=weight(kg), 76=body fat mass(kg), 11=heart rate, 54=SpO2
MEASURES = {"1": "weight_kg", "76": "fat_mass_kg", "11": "heart_rate_bpm",
            "54": "spo2_pct", "71": "body_temperature_c"}


def _token() -> str:
    token = os.environ.get("WITHINGS_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def get_body_measures(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/measure",
                          headers={"Authorization": f"Bearer {_token()}"},
                          params={"action": "getmeas",
                                  "meastypes": params.get("meastypes", "1,76,11"),
                                  "category": "1",
                                  "lastupdate": params.get("since", 0)})
    groups = []
    for g in r.get("body", {}).get("measuregrps", []):
        measures = {}
        for m in g.get("measures", []):
            name = MEASURES.get(str(m.get("type")), f"type_{m.get('type')}")
            measures[name] = m.get("value") * (10 ** m.get("unit", 0))
        groups.append({"date": g.get("date"), "measures": measures})
    return {"status": "ok", "measure_groups": groups[: int(params.get("limit", 20))]}


ACTIONS = {
    "get_body_measures": ActionDef("Read body measurements (weight, fat, HR...).",
        {"meastypes": {"type": "string", "default": "1,76,11",
                       "description": "Comma-separated Withings measure type ids"},
         "since": {"type": "integer", "default": 0, "description": "Unix timestamp lower bound"},
         "limit": {"type": "integer", "default": 20}},
        [], get_body_measures),
}

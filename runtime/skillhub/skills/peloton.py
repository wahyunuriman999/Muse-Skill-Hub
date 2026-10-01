"""Peloton driver — Peloton API implementation (unofficial endpoints).

Setup: your Peloton email + password. Set PELOTON_USERNAME and PELOTON_PASSWORD.
Note: these are unofficial endpoints Peloton's own apps use; they may change.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "peloton"
REQUIRED_ENV = ["PELOTON_USERNAME", "PELOTON_PASSWORD"]
SETUP_HELP = (
    "Set PELOTON_USERNAME and PELOTON_PASSWORD to your Peloton account credentials. "
    "Uses Peloton's unofficial API (same endpoints as their apps)."
)

_BASE = "https://api.onepeloton.com"


async def _session() -> tuple[str, str]:
    user = cred("PELOTON_USERNAME", SKILL)
    pw = cred("PELOTON_PASSWORD", SKILL)
    r = await api_request(SKILL, "POST", f"{_BASE}/auth/login",
                          json={"username_or_email": user, "password": pw})
    return r["session_id"], r["user_id"]


async def list_workouts(params: dict) -> dict:
    session_id, user_id = await _session()
    r = await api_request(SKILL, "GET", f"{_BASE}/api/user/{user_id}/workouts",
                          headers={"Cookie": f"peloton_session_id={session_id}"},
                          params={"page": 0,
                                  "limit": min(int(params.get("limit", 10)), 50),
                                  "joins": "ride"})
    return {"status": "ok", "workouts": [
        {"id": w.get("id"), "title": (w.get("ride") or {}).get("title"),
         "fitness_discipline": w.get("fitness_discipline"),
         "start_time": w.get("start_time"),
         "total_output": ((w.get("summary") or {}).get("total_output"))}
        for w in r.get("data", [])]}


ACTIONS = {
    "list_workouts": ActionDef("List recent Peloton workouts.",
        {"limit": {"type": "integer", "default": 10, "maximum": 50}},
        [], list_workouts),
}

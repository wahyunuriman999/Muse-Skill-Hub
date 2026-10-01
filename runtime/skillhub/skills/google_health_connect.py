"""Google Health Connect — local health-export reader.

Health Connect lives on-device with no cloud REST API. This driver reads a
local JSON export of Health Connect data and answers metric queries against it.

Setup: export your data to JSON and set HEALTH_CONNECT_JSON to the file path.
Expected schema: same as the apple-healthkit driver —
{"daily": [{"date": "YYYY-MM-DD", "steps": n, ...}], "sleeps": [...], "workouts": [...]}.
"""
from __future__ import annotations

import json
import os

from ..driver import ActionDef
from ..errors import SkillError

SKILL = "google-health-connect"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("Export Health Connect data to JSON and set HEALTH_CONNECT_JSON to the file path. "
              "See the module docstring for the expected schema.")


def _load() -> dict:
    path = os.environ.get("HEALTH_CONNECT_JSON")
    if not path:
        raise SkillError(SKILL, "not_configured", SETUP_HELP)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise SkillError(SKILL, "bad_export", f"Cannot read HEALTH_CONNECT_JSON: {exc}") from exc


async def get_daily_metrics(params: dict) -> dict:
    data = _load()
    days = data.get("daily", [])
    if params.get("date"):
        days = [d for d in days if d.get("date") == params["date"]]
    return {"status": "ok", "days": days[: int(params.get("limit", 7))]}


async def get_sleep(params: dict) -> dict:
    return {"status": "ok", "sleeps": _load().get("sleeps", [])[: int(params.get("limit", 7))]}


async def get_workouts(params: dict) -> dict:
    return {"status": "ok", "workouts": _load().get("workouts", [])[: int(params.get("limit", 10))]}


ACTIONS = {
    "get_daily_metrics": ActionDef("Daily metrics (steps, distance, calories, HR, HRV...).",
        {"date": {"type": "string", "description": "YYYY-MM-DD"},
         "limit": {"type": "integer", "default": 7}},
        [], get_daily_metrics),
    "get_sleep": ActionDef("Sleep sessions.",
        {"limit": {"type": "integer", "default": 7}}, [], get_sleep),
    "get_workouts": ActionDef("Workouts.",
        {"limit": {"type": "integer", "default": 10}}, [], get_workouts),
}

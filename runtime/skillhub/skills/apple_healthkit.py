"""Apple HealthKit — local health-export reader.

Apple HealthKit lives on-device with no cloud REST API. This driver reads a
local JSON export of HealthKit data and answers metric queries against it.

Setup: export your data (e.g. iPhone Health app → profile → Export, then convert
the XML to JSON, or use any exporter) and set HEALTHKIT_JSON to the file path.
Expected schema: {"daily": [{"date": "YYYY-MM-DD", "steps": n, "distance_km": f,
"active_calories": f, "resting_hr": f, "hrv_ms": f, "sleep_hours": f, ...}],
"sleeps": [{"start": iso, "end": iso, "quality": "..."}], "workouts": [...]}.
"""
from __future__ import annotations

import json
import os

from ..driver import ActionDef
from ..errors import SkillError

SKILL = "apple-healthkit"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("Export Apple Health data to JSON and set HEALTHKIT_JSON to the file path. "
              "See the module docstring for the expected schema.")


def _load() -> dict:
    path = os.environ.get("HEALTHKIT_JSON")
    if not path:
        raise SkillError(SKILL, "not_configured", SETUP_HELP)
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise SkillError(SKILL, "bad_export", f"Cannot read HEALTHKIT_JSON: {exc}") from exc


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

"""Goals — LOCAL goals-store reference implementation.

Real goal tracking (create, log progress, complete) with a local JSON store.
Reference implementation — not connected to any production goals backend.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "goals"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "goals"


def _load() -> list:
    return read_json(_STORE, [])


async def create_goal(params: dict) -> dict:
    goals = _load()
    goal = {"id": uuid.uuid4().hex[:8], "title": params["title"],
            "description": params.get("description", ""),
            "target_date": params.get("target_date"),
            "status": "active", "progress": [],
            "created_at": int(time.time())}
    goals.append(goal)
    write_json(_STORE, goals)
    return {"status": "ok", "goal": goal}


async def list_goals(params: dict) -> dict:
    goals = _load()
    if params.get("status"):
        goals = [g for g in goals if g["status"] == params["status"]]
    return {"status": "ok", "goals": goals}


async def log_progress(params: dict) -> dict:
    goals = _load()
    for g in goals:
        if g["id"] == params["goal_id"]:
            g["progress"].append({"note": params["note"],
                                  "at": int(time.time())})
            write_json(_STORE, goals)
            return {"status": "ok", "goal": g}
    raise SkillError(SKILL, "not_found", "No such goal.")


async def complete_goal(params: dict) -> dict:
    goals = _load()
    for g in goals:
        if g["id"] == params["goal_id"]:
            g["status"] = "completed"
            write_json(_STORE, goals)
            return {"status": "ok", "goal": g}
    raise SkillError(SKILL, "not_found", "No such goal.")


ACTIONS = {
    "create_goal": ActionDef("Create a goal (needs confirm=true).",
        {"title": {"type": "string"}, "description": {"type": "string"},
         "target_date": {"type": "string", "description": "YYYY-MM-DD"}},
        ["title"], create_goal, write=True),
    "list_goals": ActionDef("List goals, optionally filtered by status.",
        {"status": {"type": "string", "description": "active|completed"}},
        [], list_goals),
    "log_progress": ActionDef("Log a progress note (needs confirm=true).",
        {"goal_id": {"type": "string"}, "note": {"type": "string"}},
        ["goal_id", "note"], log_progress, write=True),
    "complete_goal": ActionDef("Mark a goal completed (needs confirm=true).",
        {"goal_id": {"type": "string"}}, ["goal_id"], complete_goal, write=True),
}

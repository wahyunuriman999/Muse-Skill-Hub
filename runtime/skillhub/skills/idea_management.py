"""Idea management — LOCAL ideas-store reference implementation.

Real CRUD for idea cards with a local JSON store. Reference implementation of
the Ideas-tab interface — not connected to any production backend.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "idea-management"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "ideas"


def _load() -> list:
    return read_json(_STORE, [])


async def add_idea(params: dict) -> dict:
    ideas = _load()
    idea = {"id": uuid.uuid4().hex[:8], "title": params["title"],
            "description": params.get("description", ""),
            "status": "new", "created_at": int(time.time())}
    ideas.append(idea)
    write_json(_STORE, ideas)
    return {"status": "ok", "idea": idea}


async def list_ideas(params: dict) -> dict:
    ideas = _load()
    if params.get("status"):
        ideas = [i for i in ideas if i["status"] == params["status"]]
    return {"status": "ok", "ideas": ideas}


async def dismiss_idea(params: dict) -> dict:
    ideas = _load()
    for i in ideas:
        if i["id"] == params["idea_id"]:
            i["status"] = "dismissed"
            write_json(_STORE, ideas)
            return {"status": "ok", "idea": i}
    raise SkillError(SKILL, "not_found", "No such idea.")


ACTIONS = {
    "add_idea": ActionDef("Add an idea card (needs confirm=true).",
        {"title": {"type": "string"}, "description": {"type": "string"}},
        ["title"], add_idea, write=True),
    "list_ideas": ActionDef("List ideas, optionally filtered by status.",
        {"status": {"type": "string", "description": "new|dismissed|done"}},
        [], list_ideas),
    "dismiss_idea": ActionDef("Dismiss an idea (needs confirm=true).",
        {"idea_id": {"type": "string"}}, ["idea_id"], dismiss_idea, write=True),
}

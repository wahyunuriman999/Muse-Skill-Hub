"""Todoist driver — real Todoist REST API implementation.

Setup: Todoist > Settings > Integrations > Developer > API token. Set TODOIST_API_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "todoist"
REQUIRED_ENV = ["TODOIST_API_TOKEN"]
SETUP_HELP = "Todoist app > Settings > Integrations > Developer tab > copy API token."

_BASE = "https://api.todoist.com/api/v1"


def _headers() -> dict:
    token = cred("TODOIST_API_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def list_tasks(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/tasks", headers=_headers(),
                          params={"limit": 20})
    items = r.get("results", []) if isinstance(r, dict) else []
    return {"status": "ok", "tasks": [
        {"id": t["id"], "content": t.get("content"), "due": (t.get("due") or {}).get("date")}
        for t in items]}


async def create_task(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/tasks", headers=_headers(),
                          json={"content": params["content"]})
    return {"status": "ok", "task": {"id": r.get("id"), "content": r.get("content")}}


ACTIONS = {
    "list_tasks": ActionDef("List Todoist tasks.", {}, [], list_tasks),
    "create_task": ActionDef("Create a task (needs confirm=true).",
        {"content": {"type": "string"}}, ["content"], create_task, write=True),
}

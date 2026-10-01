"""Asana driver — real Asana REST API implementation.

Setup: Asana > My Settings > Apps > Manage Developer Apps > Personal access token.
Set ASANA_ACCESS_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "asana"
REQUIRED_ENV = ["ASANA_ACCESS_TOKEN"]
SETUP_HELP = "Asana > profile photo > My Settings > Apps > Manage Developer Apps > personal access token."

_BASE = "https://app.asana.com/api/1.0"


def _headers() -> dict:
    token = cred("ASANA_ACCESS_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}"}


async def list_tasks(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/tasks",
                          headers=_headers(),
                          params={"project": params["project_id"],
                                  "opt_fields": "name,due_on,assignee.name,completed",
                                  "limit": 25})
    return {"status": "ok", "tasks": [
        {"gid": t["gid"], "name": t.get("name"), "due_on": t.get("due_on"),
         "completed": t.get("completed")} for t in r.get("data", [])]}


async def create_task(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/tasks", headers=_headers(),
                          json={"data": {
                              "name": params["name"],
                              "projects": [params["project_id"]],
                              "notes": params.get("notes", ""),
                              "due_on": params.get("due_on"),
                          }})
    t = r.get("data", {})
    return {"status": "ok", "task": {"gid": t.get("gid"), "name": t.get("name")}}


ACTIONS = {
    "list_tasks": ActionDef("List tasks in an Asana project.",
        {"project_id": {"type": "string", "description": "Asana project GID"}},
        ["project_id"], list_tasks),
    "create_task": ActionDef("Create a task (needs confirm=true).",
        {"project_id": {"type": "string"}, "name": {"type": "string"},
         "notes": {"type": "string", "default": ""}, "due_on": {"type": "string", "description": "YYYY-MM-DD"}},
        ["project_id", "name"], create_task, write=True),
}

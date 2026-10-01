"""Google Tasks driver — real Tasks API v1 implementation.

Setup: an OAuth2 access token with tasks scope.
Set GOOGLE_OAUTH_TOKEN (shared with the other Google drivers).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "google-tasks"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Tasks API scope "
    "(tasks), authorize, and set GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://tasks.googleapis.com/tasks/v1/users/@me"


def _headers() -> dict:
    token = os.environ.get("GOOGLE_OAUTH_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(t: dict) -> dict:
    return {"id": t.get("id"), "title": t.get("title"),
            "status": t.get("status"), "due": t.get("due"), "notes": t.get("notes")}


async def list_task_lists(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/lists", headers=_headers())
    return {"status": "ok", "lists": [
        {"id": l.get("id"), "title": l.get("title")} for l in r.get("items", [])]}


async def list_tasks(params: dict) -> dict:
    r = await api_request(SKILL, "GET",
                          f"{_BASE}/lists/{params.get('task_list_id', '@default')}/tasks",
                          headers=_headers(),
                          params={"showCompleted": str(bool(params.get("show_completed", False))).lower(),
                                  "maxResults": min(int(params.get("limit", 50)), 100)})
    return {"status": "ok", "tasks": [_fmt(t) for t in r.get("items", [])]}


async def create_task(params: dict) -> dict:
    body = {"title": params["title"]}
    if params.get("notes"):
        body["notes"] = params["notes"]
    if params.get("due"):
        body["due"] = params["due"]
    r = await api_request(SKILL, "POST",
                          f"{_BASE}/lists/{params.get('task_list_id', '@default')}/tasks",
                          headers=_headers(), json=body)
    return {"status": "ok", "task": _fmt(r)}


async def complete_task(params: dict) -> dict:
    r = await api_request(SKILL, "PATCH",
                          f"{_BASE}/lists/{params.get('task_list_id', '@default')}"
                          f"/tasks/{params['task_id']}",
                          headers=_headers(), json={"status": "completed"})
    return {"status": "ok", "task": _fmt(r)}


ACTIONS = {
    "list_task_lists": ActionDef("List task lists.", {}, [], list_task_lists),
    "list_tasks": ActionDef("List tasks in a list.",
        {"task_list_id": {"type": "string", "default": "@default"},
         "show_completed": {"type": "boolean", "default": False},
         "limit": {"type": "integer", "default": 50, "maximum": 100}},
        [], list_tasks),
    "create_task": ActionDef("Create a task (needs confirm=true). Due is RFC3339.",
        {"title": {"type": "string"}, "notes": {"type": "string"},
         "due": {"type": "string"}, "task_list_id": {"type": "string", "default": "@default"}},
        ["title"], create_task, write=True),
    "complete_task": ActionDef("Mark a task completed (needs confirm=true).",
        {"task_id": {"type": "string"}, "task_list_id": {"type": "string", "default": "@default"}},
        ["task_id"], complete_task, write=True),
}

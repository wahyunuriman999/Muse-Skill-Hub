"""Lovable driver — real official Lovable REST API.

Manages and deploys Lovable projects through the public API
(https://api.lovable.dev/v1, docs at https://docs.lovable.dev/integrations/lovable-api).

Setup: in Lovable, go to Workspace settings → Access tokens and create an
API key (format ``lov_...``; API access requires a **Business or Enterprise**
plan plus a workspace owner/admin role), then set LOVABLE_API_KEY.

Plan gate: the API returns ``402 payment_required`` when the workspace plan
does not include API access — the driver surfaces this as a clear message
instead of a raw HTTP error.

Note: the REST API manages/deploys *existing* projects. AI project creation
and editing are officially routed to the Lovable MCP server
(https://mcp.lovable.dev, OAuth, all plans) — see SKILL.md.
"""
from __future__ import annotations

from ..driver import ActionDef
from ..errors import PermissionDenied, UpstreamError
from ..http import api_request
from ..credentials import cred

SKILL = "lovable"
REQUIRED_ENV = ["LOVABLE_API_KEY"]
SETUP_HELP = (
    "In Lovable, open Workspace settings → Access tokens and create an API "
    "key (lov_...) — this requires a Business or Enterprise plan and a "
    "workspace owner/admin role — then set the LOVABLE_API_KEY environment "
    "variable."
)

_BASE = "https://api.lovable.dev/v1"
_API_VERSION = "2026-09-11"


def _headers() -> dict:
    key = cred("LOVABLE_API_KEY", SKILL)
    return {
        "Lovable-API-Key": key,
        "Lovable-Version": _API_VERSION,
    }


async def _request(method: str, path: str, **kwargs) -> dict | list:
    """api_request with a human-readable plan-gate translation for 402."""
    try:
        return await api_request(SKILL, method, f"{_BASE}{path}",
                                 headers=_headers(), **kwargs)
    except UpstreamError as exc:
        # NOTE: http.py puts provider details in exc.internal (never the
        # public message), so check both.
        haystack = str(exc) + " " + str(getattr(exc, "internal", "") or "")
        if "402" in haystack:
            raise PermissionDenied(
                "Lovable API returned 402 payment_required: this workspace's "
                "plan does not include API access. API keys require a Lovable "
                "Business or Enterprise plan (Workspace settings → Access "
                "tokens). For Free/Pro workspaces use the official Lovable "
                "MCP server at https://mcp.lovable.dev instead.",
                skill=SKILL,
            ) from exc
        raise


def _clean_project(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "status": p.get("status"),
        "visibility": p.get("visibility"),
        "preview_url": p.get("preview_url") or p.get("previewUrl"),
        "screenshot_url": p.get("screenshot_url") or p.get("screenshotUrl"),
        "created_at": p.get("created_at") or p.get("createdAt"),
        "updated_at": p.get("updated_at") or p.get("updatedAt"),
    }


def _page_params(params: dict) -> dict:
    q: dict = {}
    limit = params.get("limit")
    if limit is not None:
        q["limit"] = min(max(int(limit), 1), 100)
    if params.get("cursor"):
        q["cursor"] = params["cursor"]
    return q


def _projects_from(resp: dict | list) -> tuple[list, dict]:
    if isinstance(resp, list):
        return resp, {}
    items = resp.get("projects") or resp.get("data") or resp.get("items") or []
    page = resp.get("pagination") or {}
    return items, {
        "has_more": page.get("has_more", page.get("hasMore", False)),
        "next_cursor": page.get("next_cursor", page.get("nextCursor")),
    }


async def list_workspaces(params: dict) -> dict:
    r = await _request("GET", "/workspaces")
    items = r.get("workspaces") or r.get("data") or (r if isinstance(r, list) else [])
    return {"status": "ok", "workspaces": [
        {"id": w.get("id"), "name": w.get("name"), "plan": w.get("plan"),
         "role": w.get("role")}
        for w in items
    ]}


async def list_projects(params: dict) -> dict:
    workspace_id = params["workspace_id"]
    r = await _request("GET", f"/workspaces/{workspace_id}/projects",
                       params=_page_params(params))
    items, page = _projects_from(r)
    return {"status": "ok",
            "projects": [_clean_project(p) for p in items], **page}


async def get_project(params: dict) -> dict:
    r = await _request("GET", f"/projects/{params['project_id']}")
    project = r.get("project", r) if isinstance(r, dict) else r
    return {"status": "ok", "project": _clean_project(project)}


async def publish_project(params: dict) -> dict:
    """Publish a project (202 → deployment record). Poll get_project for
    the resulting publish state; the API does not expose a separate
    deployment-status endpoint."""
    r = await _request("POST", f"/projects/{params['project_id']}/deployments",
                       json=params.get("config") or {})
    dep = r.get("deployment", r) if isinstance(r, dict) else {}
    return {"status": "ok", "deployment": {
        "deployment_id": dep.get("deployment_id") or dep.get("id"),
        "status": dep.get("status"),
        "url": dep.get("url"),
        "note": ("Deployment accepted (202). Poll get_project for publish "
                 "state; the Lovable API exposes no deployment-status endpoint."),
    }}


async def update_project(params: dict) -> dict:
    body = {}
    if params.get("visibility"):
        body["visibility"] = params["visibility"]
    if params.get("name"):
        body["name"] = params["name"]
    r = await _request("PATCH", f"/projects/{params['project_id']}", json=body)
    project = r.get("project", r) if isinstance(r, dict) else r
    return {"status": "ok", "project": _clean_project(project)}


async def send_project_message(params: dict) -> dict:
    r = await _request("POST", f"/projects/{params['project_id']}/messages",
                       json={"message": params["message"]})
    msg = r.get("message", r) if isinstance(r, dict) else r
    return {"status": "ok", "message": msg if isinstance(msg, dict) else {"raw": msg}}


ACTIONS = {
    "list_workspaces": ActionDef(
        "List Lovable workspaces visible to the API key (id, name, plan).",
        {}, [], list_workspaces),
    "list_projects": ActionDef(
        "List/search projects in a Lovable workspace.",
        {"workspace_id": {"type": "string"},
         "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 100},
         "cursor": {"type": "string", "description": "Pagination cursor from a previous call"}},
        ["workspace_id"], list_projects),
    "get_project": ActionDef(
        "Get one Lovable project (status, publish state, preview/screenshot URLs).",
        {"project_id": {"type": "string"}},
        ["project_id"], get_project),
    "publish_project": ActionDef(
        "Publish (deploy) a Lovable project. Returns the accepted deployment; poll get_project for publish state.",
        {"project_id": {"type": "string"},
         "config": {"type": "object", "description": "Optional deployment config"}},
        ["project_id"], publish_project, write=True),
    "update_project": ActionDef(
        "Update a Lovable project (visibility and/or name).",
        {"project_id": {"type": "string"},
         "visibility": {"type": "string",
                        "description": "e.g. private, workspace_view, public",
                        "enum": ["private", "workspace_view", "public"]},
         "name": {"type": "string"}},
        ["project_id"], update_project, write=True),
    "send_project_message": ActionDef(
        "Send a chat/build message to a Lovable project's AI agent.",
        {"project_id": {"type": "string"},
         "message": {"type": "string"}},
        ["project_id", "message"], send_project_message, write=True),
}

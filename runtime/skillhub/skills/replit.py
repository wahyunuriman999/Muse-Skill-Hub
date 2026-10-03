"""Replit driver — real official Replit Admin API.

Reads workspaces, projects, deployments, usage and manages budgets through
the Replit Admin API (https://api.replit.com, docs at
https://docs.replit.com/teams/admin-api, OpenAPI at
https://api.replit.com/openapi.json).

Setup: an **account admin on a Replit Enterprise account** creates a scoped
API key, then set REPLIT_API_KEY. Regular (non-Enterprise) users cannot
create keys — for them the honest path is the official Replit MCP server
(https://mcp.replit.com/server/mcp, OAuth) — see SKILL.md.

Scope of the Admin API: reporting, governance, budgets, deployments and
compliance. It does NOT offer arbitrary project code execution or workspace
shell access, and there is no deployment-log API (logs are browser-only,
7-day retention).
"""
from __future__ import annotations

from ..driver import ActionDef
from ..errors import AuthExpired, PermissionDenied, UpstreamError
from ..http import api_request
from ..credentials import cred

SKILL = "replit"
REQUIRED_ENV = ["REPLIT_API_KEY"]
SETUP_HELP = (
    "Ask an account admin on your Replit Enterprise account to create a "
    "scoped Admin API key (https://docs.replit.com/teams/admin-api), then "
    "set the REPLIT_API_KEY environment variable. Non-Enterprise users "
    "cannot create API keys — use the official Replit MCP server at "
    "https://mcp.replit.com/server/mcp instead."
)

_BASE = "https://api.replit.com"

_ENTERPRISE_MSG = (
    "Replit Admin API authentication failed. This API is available only to "
    "account admins on Replit Enterprise accounts — regular and Core users "
    "cannot create API keys. Either use an Enterprise admin key, or use the "
    "official Replit MCP server at https://mcp.replit.com/server/mcp "
    "(OAuth, no Enterprise gate) for create/find/inspect/update/publish "
    "of Replit Apps."
)


def _headers() -> dict:
    key = cred("REPLIT_API_KEY", SKILL)
    return {"Authorization": f"Bearer {key}"}


async def _request(method: str, path: str, **kwargs) -> dict | list:
    """api_request with an Enterprise-gate translation for auth failures."""
    try:
        return await api_request(SKILL, method, f"{_BASE}{path}",
                                 headers=_headers(), **kwargs)
    except (AuthExpired, UpstreamError) as exc:
        text = str(exc)
        if "unauthenticated" in text or isinstance(exc, AuthExpired):
            raise PermissionDenied(_ENTERPRISE_MSG, skill=SKILL) from exc
        raise


def _page_params(params: dict, extra: dict | None = None) -> dict:
    q: dict = dict(extra or {})
    if params.get("limit") is not None:
        q["limit"] = min(max(int(params["limit"]), 1), 100)
    if params.get("cursor"):
        q["cursor"] = params["cursor"]
    return q


def _items_from(resp: dict | list, *keys: str) -> tuple[list, dict]:
    if isinstance(resp, list):
        return resp, {}
    items: list = []
    for k in keys:
        if isinstance(resp.get(k), list):
            items = resp[k]
            break
    else:
        items = resp.get("data") or resp.get("items") or []
    page = resp.get("pagination") or {}
    return items, {
        "has_more": page.get("hasMore", page.get("has_more", False)),
        "cursor": page.get("cursor"),
    }


async def list_workspaces(params: dict) -> dict:
    q = _page_params(params)
    if params.get("search"):
        q["search"] = params["search"]
    r = await _request("GET", "/workspaces", params=q)
    items, page = _items_from(r, "workspaces")
    return {"status": "ok", "workspaces": [
        {"id": w.get("id"), "name": w.get("name"), "slug": w.get("slug")}
        for w in items
    ], **page}


async def list_projects(params: dict) -> dict:
    q = _page_params(params)
    _aliases = {"workspace_id": "workspaceId", "has_deployment": "hasDeployment"}
    for ours, theirs in _aliases.items():
        if params.get(ours) is not None:
            q[theirs] = params[ours]
    if params.get("search"):
        q["search"] = params["search"]
    r = await _request("GET", "/projects", params=q)
    items, page = _items_from(r, "projects")
    return {"status": "ok", "projects": [
        {"id": p.get("id"), "name": p.get("name"), "slug": p.get("slug"),
         "workspace_id": p.get("workspaceId") or p.get("workspace_id"),
         "has_deployment": p.get("hasDeployment", p.get("has_deployment")),
         "updated_at": p.get("updatedAt") or p.get("updated_at")}
        for p in items
    ], **page}


async def list_deployments(params: dict) -> dict:
    q = _page_params(params)
    if params.get("project_id"):
        q["projectId"] = params["project_id"]
    if params.get("status"):
        q["status"] = params["status"]
    r = await _request("GET", "/deployments", params=q)
    items, page = _items_from(r, "deployments")
    return {"status": "ok",
            "deployments": [_clean_deployment(d) for d in items], **page}


def _clean_deployment(d: dict) -> dict:
    return {
        "id": d.get("id"),
        "project_id": d.get("projectId") or d.get("project_id"),
        "status": d.get("status"),
        "url": d.get("url"),
        "created_at": d.get("createdAt") or d.get("created_at"),
        "updated_at": d.get("updatedAt") or d.get("updated_at"),
    }


async def get_deployment(params: dict) -> dict:
    r = await _request("GET", f"/deployments/{params['deployment_id']}")
    dep = r.get("deployment", r) if isinstance(r, dict) else r
    return {"status": "ok", "deployment": _clean_deployment(dep)}


async def get_usage(params: dict) -> dict:
    q: dict = {}
    for k in ("group_by", "start_date", "end_date", "workspace_id", "project_id"):
        if params.get(k):
            q[k] = params[k]
    r = await _request("GET", "/usage", params=q)
    return {"status": "ok", "usage": r.get("usage", r) if isinstance(r, dict) else r}


async def set_budget(params: dict) -> dict:
    """Set/replace/clear a budget (the API treats budgets as idempotent
    desired-state). Requires the write:budgets scope."""
    body: dict = {}
    for k in ("name", "amount", "period", "workspace_id", "scope"):
        if params.get(k) is not None:
            body[k] = params[k]
    if params.get("clear"):
        body["clear"] = True
    r = await _request("POST", "/budgets", json=body)
    return {"status": "ok", "budget": r.get("budget", r) if isinstance(r, dict) else r}


ACTIONS = {
    "list_workspaces": ActionDef(
        "List Replit account workspaces (Enterprise Admin API).",
        {"search": {"type": "string"},
         "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 100},
         "cursor": {"type": "string", "description": "Pagination cursor from a previous call"}},
        [], list_workspaces),
    "list_projects": ActionDef(
        "List projects across Replit Team Workspaces (filters: workspace, search, deployment state).",
        {"workspace_id": {"type": "string"},
         "search": {"type": "string"},
         "has_deployment": {"type": "boolean"},
         "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 100},
         "cursor": {"type": "string"}},
        [], list_projects),
    "list_deployments": ActionDef(
        "List Replit deployments in a workspace (filters: project, status).",
        {"project_id": {"type": "string"},
         "status": {"type": "string"},
         "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 100},
         "cursor": {"type": "string"}},
        [], list_deployments),
    "get_deployment": ActionDef(
        "Get one Replit deployment's status.",
        {"deployment_id": {"type": "string"}},
        ["deployment_id"], get_deployment),
    "get_usage": ActionDef(
        "Get Replit cost/usage grouped by member, project, workspace or timeseries.",
        {"group_by": {"type": "string",
                      "description": "member | project | workspace | timeseries"},
         "start_date": {"type": "string", "description": "YYYY-MM-DD"},
         "end_date": {"type": "string", "description": "YYYY-MM-DD"},
         "workspace_id": {"type": "string"},
         "project_id": {"type": "string"}},
        [], get_usage),
    "set_budget": ActionDef(
        "Set, replace or clear a Replit budget (idempotent desired-state; needs write:budgets scope).",
        {"name": {"type": "string"},
         "amount": {"type": "number"},
         "period": {"type": "string", "description": "monthly | quarterly | ..."},
         "workspace_id": {"type": "string"},
         "scope": {"type": "string"},
         "clear": {"type": "boolean", "default": False,
                   "description": "Clear the named budget instead of setting it"}},
        [], set_budget, write=True),
}

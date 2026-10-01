"""Vercel driver — real Vercel REST API implementation.

Setup: Vercel > Settings > Tokens > create token. Set VERCEL_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "vercel"
REQUIRED_ENV = ["VERCEL_TOKEN"]
SETUP_HELP = "Vercel dashboard > Settings > Tokens > Create Token."

_BASE = "https://api.vercel.com"


def _headers() -> dict:
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}"}


async def list_projects(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/v9/projects", headers=_headers())
    return {"status": "ok", "projects": [
        {"id": p["id"], "name": p["name"], "framework": p.get("framework")}
        for p in r.get("projects", [])]}


async def list_deployments(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/v6/deployments",
                          headers=_headers(), params={"limit": 10})
    return {"status": "ok", "deployments": [
        {"id": d["uid"], "name": d.get("name"), "state": d.get("state"),
         "url": d.get("url")} for d in r.get("deployments", [])]}


ACTIONS = {
    "list_projects": ActionDef("List Vercel projects.", {}, [], list_projects),
    "list_deployments": ActionDef("List recent deployments.", {}, [], list_deployments),
}

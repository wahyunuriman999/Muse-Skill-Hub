"""Box driver — real Box API v2 implementation.

Setup: a Box developer token or OAuth access token with file scopes.
Get a developer token at https://app.box.com/developers/console (for testing).
Set BOX_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "box"
REQUIRED_ENV = ["BOX_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create an app at https://app.box.com/developers/console and generate a "
    "developer token (short-lived, for testing) or implement OAuth2. "
    "Set BOX_ACCESS_TOKEN."
)

_BASE = "https://api.box.com/2.0"


def _headers() -> dict:
    token = os.environ.get("BOX_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}"}


def _fmt(e: dict) -> dict:
    return {"id": e.get("id"), "name": e.get("name"), "type": e.get("type"),
            "size": e.get("size"), "modified_at": e.get("modified_at")}


async def list_folder(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/folders/{params.get('folder_id', '0')}/items",
                          headers=_headers(),
                          params={"limit": min(int(params.get("limit", 50)), 200)})
    return {"status": "ok", "entries": [_fmt(e) for e in r.get("entries", [])]}


async def search(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/search", headers=_headers(),
                          params={"query": params["query"],
                                  "limit": min(int(params.get("limit", 20)), 200)})
    return {"status": "ok", "entries": [_fmt(e) for e in r.get("entries", [])]}


async def get_file_info(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/files/{params['file_id']}",
                          headers=_headers())
    return {"status": "ok", "file": _fmt(r)}


ACTIONS = {
    "list_folder": ActionDef("List items in a Box folder ('0' = root).",
        {"folder_id": {"type": "string", "default": "0"},
         "limit": {"type": "integer", "default": 50, "maximum": 200}},
        [], list_folder),
    "search": ActionDef("Search Box content by query.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 200}},
        ["query"], search),
    "get_file_info": ActionDef("Get metadata for one file.",
        {"file_id": {"type": "string"}}, ["file_id"], get_file_info),
}

"""Dropbox driver — real Dropbox API v2 implementation.

Setup: an access token from a Dropbox app at https://www.dropbox.com/developers/apps
(scopes: files.metadata.read). For personal use, generate a token on the app page.
Set DROPBOX_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "dropbox"
REQUIRED_ENV = ["DROPBOX_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create an app at https://www.dropbox.com/developers/apps, enable the "
    "files.metadata.read scope, generate an access token, and set DROPBOX_ACCESS_TOKEN."
)

_API = "https://api.dropboxapi.com/2"


def _headers() -> dict:
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(e: dict) -> dict:
    return {"name": e.get("name"), "path": e.get("path_lower"),
            "type": e.get(".tag"), "size": e.get("size"),
            "modified": e.get("client_modified")}


async def list_folder(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_API}/files/list_folder",
                          headers=_headers(),
                          json={"path": params.get("path", ""),
                                "recursive": bool(params.get("recursive", False)),
                                "limit": min(int(params.get("limit", 100)), 2000)})
    return {"status": "ok", "entries": [_fmt(e) for e in r.get("entries", [])],
            "has_more": r.get("has_more", False)}


async def get_metadata(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_API}/files/get_metadata",
                          headers=_headers(),
                          json={"path": params["path"]})
    return {"status": "ok", "entry": _fmt(r)}


ACTIONS = {
    "list_folder": ActionDef("List files and folders at a Dropbox path ('' = root).",
        {"path": {"type": "string", "default": ""},
         "recursive": {"type": "boolean", "default": False},
         "limit": {"type": "integer", "default": 100, "maximum": 2000}},
        [], list_folder),
    "get_metadata": ActionDef("Get metadata for one file/folder path.",
        {"path": {"type": "string", "description": "Full Dropbox path, e.g. /docs/report.pdf"}},
        ["path"], get_metadata),
}

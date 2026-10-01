"""Figma driver — real Figma REST API implementation.

Setup: a Personal Access Token from Figma → Settings → Personal access tokens.
Set FIGMA_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "figma"
REQUIRED_ENV = ["FIGMA_ACCESS_TOKEN"]
SETUP_HELP = (
    "In Figma, open Settings → Personal access tokens, generate a token, "
    "and set FIGMA_ACCESS_TOKEN."
)

_BASE = "https://api.figma.com/v1"


def _headers() -> dict:
    token = os.environ.get("FIGMA_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"X-Figma-Token": token}


async def get_file(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/files/{params['file_key']}",
                          headers=_headers())
    doc = r.get("document", {})
    return {"status": "ok", "name": r.get("name"),
            "last_modified": r.get("lastModified"),
            "top_level_children": [c.get("name") for c in doc.get("children", [])]}


async def export_image(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/images/{params['file_key']}",
                          headers=_headers(),
                          params={"ids": params["node_ids"],
                                  "format": params.get("format", "png"),
                                  "scale": params.get("scale", 1)})
    return {"status": "ok", "images": r.get("images", {})}


ACTIONS = {
    "get_file": ActionDef("Get a Figma file's structure (file key from its URL).",
        {"file_key": {"type": "string", "description": "From the file URL after /design/"}},
        ["file_key"], get_file),
    "export_image": ActionDef("Export node(s) as image URLs.",
        {"file_key": {"type": "string"}, "node_ids": {"type": "string",
         "description": "Comma-separated node IDs"},
         "format": {"type": "string", "default": "png"},
         "scale": {"type": "integer", "default": 1}},
        ["file_key", "node_ids"], export_image),
}

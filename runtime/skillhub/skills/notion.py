"""Notion driver — real Notion REST API implementation.

Setup: notion.so/my-account/integrations > New integration, share pages with it.
Set NOTION_TOKEN (starts with ntn_ or secret_).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "notion"
REQUIRED_ENV = ["NOTION_TOKEN"]
SETUP_HELP = ("Create an integration at notion.so/my-account/integrations, "
              "share the target pages/databases with it, copy the Internal Integration Secret.")

_BASE = "https://api.notion.com/v1"


def _headers() -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"}


async def search(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/search", headers=_headers(),
                          json={"query": params["query"], "page_size": 10})
    return {"status": "ok", "results": [
        {"id": x["id"], "object": x.get("object"),
         "title": _title(x)} for x in r.get("results", [])]}


def _title(x: dict) -> str:
    props = x.get("properties", {})
    t = props.get("title", {})
    if isinstance(t, dict) and t.get("title"):
        return "".join(s.get("plain_text", "") for s in t["title"])
    return x.get("id", "")[:8]


async def query_database(params: dict) -> dict:
    r = await api_request(SKILL, "POST",
                          f"{_BASE}/databases/{params['database_id']}/query",
                          headers=_headers(), json={"page_size": 10})
    return {"status": "ok", "rows": [
        {"id": x["id"], "title": _title(x)} for x in r.get("results", [])]}


ACTIONS = {
    "search": ActionDef("Search Notion pages and databases.",
        {"query": {"type": "string"}}, ["query"], search),
    "query_database": ActionDef("Query rows of a Notion database.",
        {"database_id": {"type": "string", "description": "32-char database ID"}},
        ["database_id"], query_database),
}

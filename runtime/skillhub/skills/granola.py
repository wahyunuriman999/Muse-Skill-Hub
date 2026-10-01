"""Granola driver — real official Granola public API.

Lists meeting notes and reads full transcripts through Granola's public API
(https://public-api.granola.ai/v1, docs at https://docs.granola.ai).

Setup: in Granola, create an API key (format ``grn_...``; API access requires
a Granola plan that includes it) and set GRANOLA_API_KEY.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "granola"
REQUIRED_ENV = ["GRANOLA_API_KEY"]
SETUP_HELP = (
    "In Granola, create an API key (grn_...) — API access requires a Granola "
    "plan that includes it — then set the GRANOLA_API_KEY environment variable."
)

_BASE = "https://public-api.granola.ai/v1"


def _headers() -> dict:
    key = os.environ.get("GRANOLA_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {key}"}


def _clean_note(n: dict) -> dict:
    owner = n.get("owner") or {}
    return {
        "id": n.get("id"),
        "title": n.get("title"),
        "owner_name": owner.get("name"),
        "owner_email": owner.get("email"),
        "created_at": n.get("created_at"),
        "updated_at": n.get("updated_at"),
        "url": f"https://notes.granola.ai/d/{n.get('id')}" if n.get("id") else None,
    }


async def list_notes(params: dict) -> dict:
    q: dict = {}
    for k in ("created_after", "created_before", "updated_after", "folder_id", "cursor"):
        if params.get(k):
            q[k] = params[k]
    q["page_size"] = min(max(int(params.get("page_size", 10)), 1), 30)
    r = await api_request(SKILL, "GET", f"{_BASE}/notes",
                          headers=_headers(), params=q)
    return {"status": "ok",
            "notes": [_clean_note(n) for n in r.get("notes", [])],
            "has_more": r.get("hasMore"),
            "cursor": r.get("cursor")}


async def get_note(params: dict) -> dict:
    note_id = params["note_id"]
    q = {"include": "transcript"} if params.get("include_transcript", True) else {}
    r = await api_request(SKILL, "GET", f"{_BASE}/notes/{note_id}",
                          headers=_headers(), params=q)
    out = _clean_note(r)
    # The detail endpoint returns the note object; summary/transcript fields
    # are passed through when present.
    for k in ("summary", "transcript", "notes", "action_items"):
        if r.get(k) is not None:
            out[k] = r[k]
    out["raw"] = {k: v for k, v in r.items() if k not in out}
    return {"status": "ok", "note": out}


async def search_notes(params: dict) -> dict:
    """Client-side title search over list_notes pages (the API has no
    server-side query parameter)."""
    query = params["query"].lower()
    limit = min(int(params.get("limit", 10)), 30)
    found, cursor, pages = [], None, 0
    headers = _headers()
    while len(found) < limit and pages < 5:
        q: dict = {"page_size": 30}
        if cursor:
            q["cursor"] = cursor
        r = await api_request(SKILL, "GET", f"{_BASE}/notes",
                              headers=headers, params=q)
        for n in r.get("notes", []):
            if query in (n.get("title") or "").lower():
                found.append(_clean_note(n))
                if len(found) >= limit:
                    break
        if not r.get("hasMore"):
            break
        cursor = r.get("cursor")
        pages += 1
    return {"status": "ok", "notes": found[:limit],
            "note": "client-side title filter; the Granola API has no search endpoint"}


ACTIONS = {
    "list_notes": ActionDef(
        "List Granola meeting notes (newest API pages; supports date/folder filters).",
        {"created_after": {"type": "string", "description": "YYYY-MM-DD"},
         "created_before": {"type": "string", "description": "YYYY-MM-DD"},
         "updated_after": {"type": "string", "description": "YYYY-MM-DD"},
         "folder_id": {"type": "string"},
         "cursor": {"type": "string", "description": "Pagination cursor from a previous call"},
         "page_size": {"type": "integer", "default": 10, "minimum": 1, "maximum": 30}},
        [], list_notes),
    "get_note": ActionDef(
        "Read one Granola note with its AI summary and (optionally) full transcript.",
        {"note_id": {"type": "string"},
         "include_transcript": {"type": "boolean", "default": True}},
        ["note_id"], get_note),
    "search_notes": ActionDef(
        "Search Granola notes by title substring (client-side filter over recent notes).",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 10, "maximum": 30}},
        ["query"], search_notes),
}

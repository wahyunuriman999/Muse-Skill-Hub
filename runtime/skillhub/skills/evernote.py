"""Evernote driver — Evernote Cloud API via the official Python SDK.

Setup: pip install evernote3, then create a developer token at
https://www.evernote.com/api/DeveloperToken.action (sandbox or production).
Set EVERNOTE_DEV_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing, SkillError

SKILL = "evernote"
REQUIRED_ENV = ["EVERNOTE_DEV_TOKEN"]
SETUP_HELP = (
    "pip install evernote3, then get a developer token at "
    "https://www.evernote.com/api/DeveloperToken.action and set EVERNOTE_DEV_TOKEN."
)


def _client():
    token = os.environ.get("EVERNOTE_DEV_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    try:
        from evernote.api.client import EvernoteClient
    except ImportError as exc:
        raise SkillError(SKILL, "missing dependency",
                         "pip install evernote3 to enable the Evernote driver.") from exc
    return EvernoteClient(token=token, sandbox=False)


async def list_notebooks(params: dict) -> dict:
    store = _client().get_note_store()
    notebooks = store.listNotebooks()
    return {"status": "ok", "notebooks": [
        {"guid": n.guid, "name": n.name} for n in notebooks]}


async def list_notes(params: dict) -> dict:
    from evernote.edam.notestore.ttypes import NoteFilter
    store = _client().get_note_store()
    nf = NoteFilter(notebookGuid=params.get("notebook_guid"),
                    words=params.get("query"), order=2)
    result = store.findNotes(nf, 0, min(int(params.get("limit", 20)), 100))
    return {"status": "ok", "total": result.totalNotes, "notes": [
        {"guid": n.guid, "title": n.title, "created": n.created}
        for n in result.notes]}


ACTIONS = {
    "list_notebooks": ActionDef("List Evernote notebooks.", {}, [], list_notebooks),
    "list_notes": ActionDef("Search notes (optionally in one notebook).",
        {"query": {"type": "string", "description": "Evernote search grammar"},
         "notebook_guid": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_notes),
}

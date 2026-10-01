"""Google Docs driver — real Docs API v1 implementation.

Setup: an OAuth2 access token with documents scope.
Set GOOGLE_OAUTH_TOKEN (shared with the other Google drivers).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "google-docs"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Docs API scope "
    "(documents), authorize, and set GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://docs.googleapis.com/v1/documents"


def _headers() -> dict:
    token = cred("GOOGLE_OAUTH_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _text_of(doc: dict) -> str:
    parts = []
    for el in (doc.get("body") or {}).get("content", []):
        para = el.get("paragraph")
        if not para:
            continue
        for pe in para.get("elements", []):
            tr = pe.get("textRun")
            if tr:
                parts.append(tr.get("content", ""))
    return "".join(parts)


async def get_document(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['document_id']}",
                          headers=_headers())
    return {"status": "ok", "title": r.get("title"),
            "text": _text_of(r)[:8000]}


async def create_document(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"title": params["title"]})
    doc_id = r.get("documentId")
    if params.get("text"):
        await api_request(SKILL, "POST", f"{_BASE}/{doc_id}:batchUpdate",
                          headers=_headers(),
                          json={"requests": [{"insertText": {
                              "location": {"index": 1},
                              "text": params["text"]}}]})
    return {"status": "ok", "document_id": doc_id, "title": params["title"]}


ACTIONS = {
    "get_document": ActionDef("Read a Google Doc's text (ID from its URL).",
        {"document_id": {"type": "string"}}, ["document_id"], get_document, required_scopes=["https://www.googleapis.com/auth/documents.readonly"]),
    "create_document": ActionDef("Create a doc, optionally with initial text (needs confirm=true).",
        {"title": {"type": "string"}, "text": {"type": "string"}},
        ["title"], create_document, write=True, required_scopes=["https://www.googleapis.com/auth/documents"]),
}

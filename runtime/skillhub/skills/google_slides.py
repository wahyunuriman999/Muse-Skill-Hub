"""Google Slides driver — real Slides API v1 implementation.

Setup: an OAuth2 access token with presentations scope.
Set GOOGLE_OAUTH_TOKEN (shared with the other Google drivers).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "google-slides"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Slides API scope "
    "(presentations), authorize, and set GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://slides.googleapis.com/v1/presentations"


def _headers() -> dict:
    token = cred("GOOGLE_OAUTH_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def get_presentation(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['presentation_id']}",
                          headers=_headers())
    slides = r.get("slides", [])
    return {"status": "ok", "title": r.get("title"),
            "slide_count": len(slides),
            "slides": [{"objectId": s.get("objectId")} for s in slides[:50]]}


async def create_presentation(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"title": params["title"]})
    return {"status": "ok", "presentation_id": r.get("presentationId"),
            "title": params["title"]}


ACTIONS = {
    "get_presentation": ActionDef("Read a presentation's metadata and slide list.",
        {"presentation_id": {"type": "string", "description": "ID from its URL"}},
        ["presentation_id"], get_presentation, required_scopes=["https://www.googleapis.com/auth/presentations.readonly"]),
    "create_presentation": ActionDef("Create a blank presentation (needs confirm=true).",
        {"title": {"type": "string"}}, ["title"], create_presentation, write=True, required_scopes=["https://www.googleapis.com/auth/presentations"]),
}

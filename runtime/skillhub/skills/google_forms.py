"""Google Forms driver — real Forms API v1 implementation.

Setup: an OAuth2 access token with forms scopes.
Set GOOGLE_OAUTH_TOKEN (shared with the other Google drivers).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "google-forms"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Forms API scopes "
    "(forms.body, forms.responses.readonly), authorize, and set GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://forms.googleapis.com/v1/forms"


def _headers() -> dict:
    token = cred("GOOGLE_OAUTH_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def create_form(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"info": {"title": params["title"]}})
    return {"status": "ok", "form_id": r.get("formId"),
            "responder_uri": r.get("responderUri")}


async def get_responses(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['form_id']}/responses",
                          headers=_headers())
    responses = r.get("responses", [])
    return {"status": "ok", "count": len(responses),
            "responses": [{"responseId": x.get("responseId"),
                           "answers": x.get("answers", {})}
                          for x in responses[:50]]}


ACTIONS = {
    "create_form": ActionDef("Create an empty Google Form (needs confirm=true).",
        {"title": {"type": "string"}}, ["title"], create_form, write=True, required_scopes=["https://www.googleapis.com/auth/forms.body"]),
    "get_responses": ActionDef("Read a form's responses.",
        {"form_id": {"type": "string"}}, ["form_id"], get_responses, required_scopes=["https://www.googleapis.com/auth/forms.body.readonly"]),
}

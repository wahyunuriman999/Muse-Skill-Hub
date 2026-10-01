"""Meta Threads driver — real Threads API implementation.

Setup: a Threads user access token with scopes (threads_basic, threads_content_publish).
Create a Meta app at https://developers.facebook.com, add the Threads use case,
and authorize a Threads account. Set THREADS_ACCESS_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "meta-threads"
REQUIRED_ENV = ["THREADS_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, add the Threads use case, "
    "authorize with scopes threads_basic and threads_content_publish, "
    "and set THREADS_ACCESS_TOKEN."
)

_BASE = "https://graph.threads.net/v1.0"


def _token() -> str:
    token = cred("THREADS_ACCESS_TOKEN", SKILL)
    return token


async def get_profile(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me",
                          params={"fields": "id,username,threads_profile_picture_url",
                                  "access_token": _token()})
    return {"status": "ok", "profile": r}


async def post_text(params: dict) -> dict:
    token = _token()
    created = await api_request(SKILL, "POST", f"{_BASE}/me/threads",
                                params={"media_type": "TEXT", "text": params["text"],
                                        "access_token": token})
    published = await api_request(SKILL, "POST", f"{_BASE}/me/threads_publish",
                                  params={"creation_id": created.get("id"),
                                          "access_token": token})
    return {"status": "ok", "creation_id": created.get("id"),
            "post_id": published.get("id")}


ACTIONS = {
    "get_profile": ActionDef("Get the connected Threads profile.",
        {}, [], get_profile),
    "post_text": ActionDef("Publish a text post (two-step create+publish; needs confirm=true).",
        {"text": {"type": "string", "maxLength": 500}},
        ["text"], post_text, write=True),
}

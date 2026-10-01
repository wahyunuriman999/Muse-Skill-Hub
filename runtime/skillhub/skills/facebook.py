"""Facebook driver — real Facebook Graph API implementation.

Setup: a user or Page access token with scopes (pages_read_engagement, pages_manage_posts,
public_profile). Create a Meta app at https://developers.facebook.com and authorize.
Set FACEBOOK_ACCESS_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "facebook"
REQUIRED_ENV = ["FACEBOOK_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, authorize with the needed "
    "scopes (public_profile, pages_read_engagement, pages_manage_posts), "
    "and set FACEBOOK_ACCESS_TOKEN."
)

_BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    token = cred("FACEBOOK_ACCESS_TOKEN", SKILL)
    return token


async def get_profile(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me",
                          params={"fields": "id,name", "access_token": _token()})
    return {"status": "ok", "profile": r}


async def get_posts(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/posts",
                          params={"fields": "id,message,created_time,permalink_url",
                                  "limit": min(int(params.get("limit", 10)), 50),
                                  "access_token": _token()})
    return {"status": "ok", "posts": r.get("data", [])}


async def post_to_feed(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/me/feed",
                          params={"message": params["message"],
                                  "access_token": _token()})
    return {"status": "ok", "post_id": r.get("id")}


ACTIONS = {
    "get_profile": ActionDef("Get the connected Facebook profile.",
        {}, [], get_profile),
    "get_posts": ActionDef("List recent posts from the profile/Page feed.",
        {"limit": {"type": "integer", "default": 10, "maximum": 50}},
        [], get_posts),
    "post_to_feed": ActionDef("Publish a post to the feed (needs confirm=true).",
        {"message": {"type": "string"}},
        ["message"], post_to_feed, write=True),
}

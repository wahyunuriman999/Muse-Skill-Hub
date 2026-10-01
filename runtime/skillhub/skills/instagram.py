"""Instagram driver — real Instagram Graph API implementation.

Setup: a long-lived Instagram user access token with scopes
(instagram_business_basic, instagram_business_content_publish for posting).
Create a Meta app at https://developers.facebook.com, add the Instagram product,
and authorize a business/creator account. Set INSTAGRAM_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "instagram"
REQUIRED_ENV = ["INSTAGRAM_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, add the Instagram product, "
    "connect an Instagram business/creator account, authorize with scopes "
    "instagram_business_basic (+ instagram_business_content_publish to post), "
    "and set INSTAGRAM_ACCESS_TOKEN."
)

_BASE = "https://graph.instagram.com/v21.0"


def _token() -> str:
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def get_profile(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me",
                          params={"fields": "id,username,account_type,media_count",
                                  "access_token": _token()})
    return {"status": "ok", "profile": r}


async def get_media(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/media",
                          params={"fields": "id,caption,media_type,timestamp,permalink,like_count",
                                  "limit": min(int(params.get("limit", 10)), 50),
                                  "access_token": _token()})
    return {"status": "ok", "media": r.get("data", [])}


ACTIONS = {
    "get_profile": ActionDef("Get the connected Instagram account's profile.",
        {}, [], get_profile),
    "get_media": ActionDef("List recent media posts.",
        {"limit": {"type": "integer", "default": 10, "maximum": 50}},
        [], get_media),
}

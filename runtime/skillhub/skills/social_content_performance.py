"""Social content performance driver — real Instagram Graph insights.

Reads reach/impressions/profile-activity for the connected Instagram business
account and per-media insights. Set INSTAGRAM_ACCESS_TOKEN (shared with the
instagram driver).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "social-content-performance"
REQUIRED_ENV = ["INSTAGRAM_ACCESS_TOKEN"]
SETUP_HELP = (
    "Connect an Instagram business/creator account via a Meta app "
    "(https://developers.facebook.com) with instagram_business_basic scope, "
    "and set INSTAGRAM_ACCESS_TOKEN."
)

_BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    token = cred("INSTAGRAM_ACCESS_TOKEN", SKILL)
    return token


async def account_insights(params: dict) -> dict:
    user = params.get("ig_user_id", "me")
    r = await api_request(SKILL, "GET", f"{_BASE}/{user}/insights",
                          params={"metric": "reach,impressions,profile_views",
                                  "period": "day",
                                  "access_token": _token()})
    out = {}
    for m in r.get("data", []):
        vals = m.get("values", [])
        out[m.get("name")] = vals[-1].get("value") if vals else None
    return {"status": "ok", "insights": out}


async def media_insights(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/{params['media_id']}/insights",
                          params={"metric": "reach,impressions,likes,comments,shares,saves",
                                  "access_token": _token()})
    return {"status": "ok", "insights": {
        m.get("name"): (m.get("values", [{}])[0].get("value"))
        for m in r.get("data", [])}}


ACTIONS = {
    "account_insights": ActionDef("Account-level reach/impressions/profile views.",
        {"ig_user_id": {"type": "string", "default": "me",
                        "description": "Instagram business account ID"}},
        [], account_insights),
    "media_insights": ActionDef("Per-post reach, likes, comments, shares, saves.",
        {"media_id": {"type": "string"}},
        ["media_id"], media_insights),
}

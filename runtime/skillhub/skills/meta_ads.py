"""Meta Ads driver — real Meta Marketing API implementation.

Setup: a user access token with ads_read (and ads_management to manage) from a
Meta app at https://developers.facebook.com. Set META_ADS_ACCESS_TOKEN.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "meta-ads"
REQUIRED_ENV = ["META_ADS_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create a Meta app at https://developers.facebook.com, add the Marketing API, "
    "authorize with ads_read (and ads_management to create/manage), "
    "and set META_ADS_ACCESS_TOKEN."
)

_BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    token = os.environ.get("META_ADS_ACCESS_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return token


async def list_ad_accounts(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/adaccounts",
                          params={"fields": "id,name,account_status,currency",
                                  "limit": min(int(params.get("limit", 25)), 100),
                                  "access_token": _token()})
    return {"status": "ok", "ad_accounts": r.get("data", [])}


async def list_campaigns(params: dict) -> dict:
    r = await api_request(SKILL, "GET",
                          f"{_BASE}/act_{params['ad_account_id']}/campaigns",
                          params={"fields": "id,name,status,objective",
                                  "limit": min(int(params.get("limit", 25)), 100),
                                  "access_token": _token()})
    return {"status": "ok", "campaigns": r.get("data", [])}


ACTIONS = {
    "list_ad_accounts": ActionDef("List ad accounts the token can access.",
        {"limit": {"type": "integer", "default": 25, "maximum": 100}},
        [], list_ad_accounts),
    "list_campaigns": ActionDef("List campaigns in an ad account.",
        {"ad_account_id": {"type": "string", "description": "Numeric ID without act_ prefix"},
         "limit": {"type": "integer", "default": 25, "maximum": 100}},
        ["ad_account_id"], list_campaigns),
}

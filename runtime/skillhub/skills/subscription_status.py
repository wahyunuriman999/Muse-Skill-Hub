"""Subscription status — local runtime subscription-config reporter.

Reports the subscription configuration this runtime knows about (from local
config/env). It cannot see your actual Muse subscription — that lives in the
product's account system, which has no public API. Honest about the boundary.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..localstore import read_json

SKILL = "subscription-status"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("No credentials — reports local config only. "
              "Live subscription/usage data lives in the product account system "
              "and has no public API.")


async def get_status(params: dict) -> dict:
    cfg = read_json("subscription", {})
    return {"status": "ok",
            "plan": cfg.get("plan") or os.environ.get("SKILLHUB_PLAN", "unknown"),
            "source": "local runtime config",
            "note": ("This reflects local configuration only. Your real Muse plan, "
                     "usage, and reset timing are shown in the product's account settings.")}


ACTIONS = {
    "get_status": ActionDef("Report the runtime's local subscription configuration.",
        {}, [], get_status),
}

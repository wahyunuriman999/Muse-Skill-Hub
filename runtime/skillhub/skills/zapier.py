"""Zapier driver — trigger Zaps via Zapier Webhooks.

Setup: in Zapier, create a Zap with a "Webhooks by Zapier" trigger
("Catch Hook"), copy the webhook URL, and set ZAPIER_WEBHOOK_URL.
Calling trigger_zap POSTs your payload to that Zap (needs confirm=true).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "zapier"
REQUIRED_ENV = ["ZAPIER_WEBHOOK_URL"]
SETUP_HELP = (
    "In Zapier, make a Zap with trigger 'Webhooks by Zapier' → 'Catch Hook', "
    "copy the webhook URL, and set ZAPIER_WEBHOOK_URL."
)


def _url() -> str:
    url = os.environ.get("ZAPIER_WEBHOOK_URL")
    if not url:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return url


async def trigger_zap(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _url(), json=params.get("payload", {}))
    return {"status": "ok", "zap_response": r}


ACTIONS = {
    "trigger_zap": ActionDef("POST a JSON payload to your Zapier Catch Hook (needs confirm=true).",
        {"payload": {"type": "object", "description": "JSON payload for the Zap"}},
        [], trigger_zap, write=True),
}

"""Tailscale driver — real Tailscale API implementation.

Setup: an API key from https://login.tailscale.com/admin/settings/keys
(tag it, give it devices:read scope or broader). Set TAILSCALE_API_KEY and
TAILSCALE_TAILNET (your tailnet name, e.g. 'example.com').
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "tailscale"
REQUIRED_ENV = ["TAILSCALE_API_KEY", "TAILSCALE_TAILNET"]
SETUP_HELP = (
    "Generate an API key at https://login.tailscale.com/admin/settings/keys and set "
    "TAILSCALE_API_KEY plus TAILSCALE_TAILNET (your tailnet domain)."
)

_BASE = "https://api.tailscale.com"


def _ctx() -> tuple[dict, str]:
    key = os.environ.get("TAILSCALE_API_KEY")
    tailnet = os.environ.get("TAILSCALE_TAILNET")
    if not key or not tailnet:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {key}"}, tailnet


async def list_devices(params: dict) -> dict:
    headers, tailnet = _ctx()
    r = await api_request(SKILL, "GET", f"{_BASE}/tailnet/{tailnet}/devices",
                          headers=headers)
    devices = r.get("devices", [])
    return {"status": "ok", "devices": [
        {"name": d.get("name"), "hostname": d.get("hostname"),
         "os": d.get("os"), "addresses": d.get("addresses"),
         "lastSeen": d.get("lastSeen")}
        for d in devices]}


ACTIONS = {
    "list_devices": ActionDef("List devices on the tailnet.",
        {}, [], list_devices),
}

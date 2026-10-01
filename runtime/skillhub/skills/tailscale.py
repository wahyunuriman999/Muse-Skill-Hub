"""Tailscale driver — real Tailscale API implementation.

Setup: an API key from https://login.tailscale.com/admin/settings/keys
(tag it, give it devices:read scope or broader). Set TAILSCALE_API_KEY and
TAILSCALE_TAILNET (your tailnet name, e.g. 'example.com').
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "tailscale"
REQUIRED_ENV = ["TAILSCALE_API_KEY", "TAILSCALE_TAILNET"]
SETUP_HELP = (
    "Generate an API key at https://login.tailscale.com/admin/settings/keys and set "
    "TAILSCALE_API_KEY plus TAILSCALE_TAILNET (your tailnet domain)."
)

_BASE = "https://api.tailscale.com"


def _ctx() -> tuple[dict, str]:
    key = cred("TAILSCALE_API_KEY", SKILL)
    tailnet = cred("TAILSCALE_TAILNET", SKILL)
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

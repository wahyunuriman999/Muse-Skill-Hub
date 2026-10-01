"""Messaging channels — channel registry + webhook dispatcher.

Register messaging channels (each with an outbound webhook URL) and dispatch
messages through them. Real dispatch logic — but delivery requires you to
configure each channel's webhook (e.g. a WhatsApp Business webhook). Channels
without a configured webhook return an honest not-configured error.
"""
from __future__ import annotations

import time

from ..driver import ActionDef
from ..errors import SkillError
from ..http import api_request
from ..localstore import read_json, write_json

SKILL = "messaging-channels"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("Register channels with register_channel including a webhook_url; "
              "send_message POSTs to that webhook.")

_STORE = "channels"


def _load() -> dict:
    return read_json(_STORE, {})


async def register_channel(params: dict) -> dict:
    channels = _load()
    channels[params["name"]] = {"name": params["name"],
                                "provider": params.get("provider", ""),
                                "webhook_url": params.get("webhook_url", ""),
                                "registered_at": int(time.time())}
    write_json(_STORE, channels)
    return {"status": "ok", "channel": channels[params["name"]]}


async def list_channels(params: dict) -> dict:
    return {"status": "ok", "channels": list(_load().values())}


async def send_message(params: dict) -> dict:
    channel = _load().get(params["channel"])
    if not channel:
        raise SkillError(SKILL, "not_found", "No such channel.")
    if not channel.get("webhook_url"):
        raise SkillError(SKILL, "not_configured",
                         f"Channel '{params['channel']}' has no webhook_url configured.")
    r = await api_request(SKILL, "POST", channel["webhook_url"],
                          json={"to": params["to"], "text": params["text"]})
    return {"status": "ok", "channel": params["channel"], "response": r}


ACTIONS = {
    "register_channel": ActionDef("Register a channel (needs confirm=true).",
        {"name": {"type": "string"}, "provider": {"type": "string"},
         "webhook_url": {"type": "string"}},
        ["name"], register_channel, write=True),
    "list_channels": ActionDef("List registered channels.", {}, [], list_channels),
    "send_message": ActionDef("Dispatch a message via a channel's webhook (needs confirm=true).",
        {"channel": {"type": "string"}, "to": {"type": "string"}, "text": {"type": "string"}},
        ["channel", "to", "text"], send_message, write=True),
}

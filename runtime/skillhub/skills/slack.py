"""Slack driver — real Slack Web API implementation.

Setup: create a Slack app, add a Bot Token (starts with 'xoxb'), set SLACK_BOT_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "slack"
REQUIRED_ENV = ["SLACK_BOT_TOKEN"]
SETUP_HELP = (
    "Create a Slack app at https://api.slack.com/apps, install it to your workspace, "
    "and copy the Bot User OAuth Token (starts with 'xoxb')."
)

_BASE = "https://slack.com/api"


def _headers() -> dict:
    token = cred("SLACK_BOT_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _ok(resp: dict) -> dict:
    if isinstance(resp, dict) and resp.get("ok") is False:
        from ..errors import UpstreamError

        raise UpstreamError(SKILL, resp.get("error", "slack api error"))
    return resp


async def list_channels(params: dict) -> dict:
    r = await _ok(await api_request(SKILL, "GET", f"{_BASE}/conversations.list",
                                   headers=_headers(),
                                   params={"types": "public_channel,private_channel", "limit": 50}))
    return {"status": "ok", "channels": [
        {"id": c["id"], "name": c.get("name"), "members": c.get("num_members")}
        for c in r.get("channels", [])]}


async def read_channel(params: dict) -> dict:
    r = await _ok(await api_request(SKILL, "GET", f"{_BASE}/conversations.history",
                                    headers=_headers(),
                                    params={"channel": params["channel_id"],
                                            "limit": min(int(params.get("limit", 10)), 50)}))
    return {"status": "ok", "messages": [
        {"ts": m.get("ts"), "user": m.get("user"), "text": m.get("text")}
        for m in r.get("messages", [])]}


async def send_message(params: dict) -> dict:
    r = await _ok(await api_request(SKILL, "POST", f"{_BASE}/chat.postMessage",
                                    headers=_headers(),
                                    json={"channel": params["channel_id"],
                                          "text": params["text"]}))
    return {"status": "ok", "ts": r.get("ts"), "channel": r.get("channel")}


ACTIONS = {
    "list_channels": ActionDef("List workspace channels.",
        {}, [], list_channels),
    "read_channel": ActionDef("Read recent messages from a channel.",
        {"channel_id": {"type": "string", "description": "Channel ID, e.g. C012AB345CD"},
         "limit": {"type": "integer", "default": 10, "maximum": 50}},
        ["channel_id"], read_channel),
    "send_message": ActionDef("Send a message to a channel (needs confirm=true).",
        {"channel_id": {"type": "string"}, "text": {"type": "string"}},
        ["channel_id", "text"], send_message, write=True),
}

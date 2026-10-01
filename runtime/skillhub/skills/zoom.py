"""Zoom driver — real Zoom API with Server-to-Server OAuth.

Setup: Zoom Marketplace > Build App > Server-to-Server OAuth, add scopes
(meeting:read, meeting:write). Set ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET,
ZOOM_ACCOUNT_ID.
"""
from __future__ import annotations

import base64
import time

from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "zoom"
REQUIRED_ENV = ["ZOOM_CLIENT_ID", "ZOOM_CLIENT_SECRET", "ZOOM_ACCOUNT_ID"]
SETUP_HELP = ("Zoom Marketplace (marketplace.zoom.us) > Develop > Build App > "
              "Server-to-Server OAuth > add meeting scopes > copy credentials.")

_token_cache: dict = {}


async def _token() -> str:
    cid = cred("ZOOM_CLIENT_ID", SKILL)
    secret = cred("ZOOM_CLIENT_SECRET", SKILL)
    aid = cred("ZOOM_ACCOUNT_ID", SKILL)
    if _token_cache.get("exp", 0) > time.time() + 60:
        return _token_cache["token"]
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    r = await api_request(SKILL, "POST", "https://zoom.us/oauth/token",
                          headers={"Authorization": f"Basic {basic}"},
                          params={"grant_type": "account_credentials", "account_id": aid})
    _token_cache.update({"token": r["access_token"], "exp": time.time() + r.get("expires_in", 3600)})
    return _token_cache["token"]


async def _headers() -> dict:
    return {"Authorization": f"Bearer {await _token()}", "Content-Type": "application/json"}


async def list_meetings(params: dict) -> dict:
    r = await api_request(SKILL, "GET", "https://api.zoom.us/v2/users/me/meetings",
                          headers=await _headers(),
                          params={"type": "upcoming", "page_size": 10})
    return {"status": "ok", "meetings": [
        {"id": m["id"], "topic": m.get("topic"), "start_time": m.get("start_time"),
         "join_url": m.get("join_url")} for m in r.get("meetings", [])]}


async def create_meeting(params: dict) -> dict:
    r = await api_request(SKILL, "POST", "https://api.zoom.us/v2/users/me/meetings",
                          headers=await _headers(),
                          json={"topic": params["topic"],
                                "type": 2,
                                "start_time": params.get("start_time"),
                                "duration": int(params.get("duration_min", 60))})
    return {"status": "ok", "meeting": {
        "id": r.get("id"), "topic": r.get("topic"),
        "join_url": r.get("join_url"), "start_time": r.get("start_time")}}


ACTIONS = {
    "list_meetings": ActionDef("List upcoming Zoom meetings.", {}, [], list_meetings),
    "create_meeting": ActionDef("Schedule a Zoom meeting (needs confirm=true).",
        {"topic": {"type": "string"},
         "start_time": {"type": "string", "description": "ISO-8601, e.g. 2026-10-02T10:00:00"},
         "duration_min": {"type": "integer", "default": 60}},
        ["topic"], create_meeting, write=True),
}

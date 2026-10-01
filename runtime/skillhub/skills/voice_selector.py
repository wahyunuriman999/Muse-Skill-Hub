"""Voice selector driver — real ElevenLabs voice catalog.

Setup: an API key from https://elevenlabs.io/app/settings/api-keys.
Set ELEVENLABS_API_KEY (shared with the tts driver).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "voice-selector"
REQUIRED_ENV = ["ELEVENLABS_API_KEY"]
SETUP_HELP = (
    "Sign up at https://elevenlabs.io, copy an API key from "
    "https://elevenlabs.io/app/settings/api-keys, and set ELEVENLABS_API_KEY."
)

_BASE = "https://api.elevenlabs.io/v1"


def _headers() -> dict:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"xi-api-key": key}


async def list_voices(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/voices", headers=_headers())
    voices = r.get("voices", [])
    if params.get("query"):
        q = params["query"].lower()
        voices = [v for v in voices if q in (v.get("name") or "").lower()
                  or q in (v.get("description") or "").lower()]
    return {"status": "ok", "voices": [
        {"voice_id": v.get("voice_id"), "name": v.get("name"),
         "description": v.get("description"), "category": v.get("category")}
        for v in voices[:50]]}


ACTIONS = {
    "list_voices": ActionDef("Browse/select a voice, optionally filtered by text.",
        {"query": {"type": "string", "description": "e.g. 'warm female narrator'"}},
        [], list_voices),
}

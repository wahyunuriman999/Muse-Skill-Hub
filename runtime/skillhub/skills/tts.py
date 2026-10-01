"""Text-to-speech driver — real ElevenLabs API implementation.

Setup: an API key from https://elevenlabs.io/app/settings/api-keys.
Set ELEVENLABS_API_KEY. Audio is returned as base64-encoded MP3.
"""
from __future__ import annotations

import base64

from ..driver import ActionDef
from ..http import api_request, raw_request
from ..credentials import cred

SKILL = "tts"
REQUIRED_ENV = ["ELEVENLABS_API_KEY"]
SETUP_HELP = (
    "Sign up at https://elevenlabs.io, copy an API key from "
    "https://elevenlabs.io/app/settings/api-keys, and set ELEVENLABS_API_KEY."
)

_BASE = "https://api.elevenlabs.io/v1"


def _headers() -> dict:
    key = cred("ELEVENLABS_API_KEY", SKILL)
    return {"xi-api-key": key, "Content-Type": "application/json"}


async def _synthesize_bytes(voice_id: str, text: str) -> bytes:
    return await raw_request(SKILL, "POST", f"{_BASE}/text-to-speech/{voice_id}",
                            headers=_headers(),
                            json={"text": text, "model_id": "eleven_multilingual_v2"})


async def _synthesize(voice_id: str, text: str) -> dict:
    audio = await _synthesize_bytes(voice_id, text)
    return {"status": "ok", "voice_id": voice_id,
            "audio_base64_mp3": base64.b64encode(audio).decode("ascii"),
            "bytes": len(audio)}


async def synthesize(params: dict) -> dict:
    return await _synthesize(params["voice_id"], params["text"])


async def list_voices(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/voices", headers=_headers())
    return {"status": "ok", "voices": [
        {"voice_id": v.get("voice_id"), "name": v.get("name"),
         "category": v.get("category")}
        for v in r.get("voices", [])]}


ACTIONS = {
    "synthesize": ActionDef("Turn text into spoken audio (MP3, base64). Needs confirm=true.",
        {"voice_id": {"type": "string", "description": "From list_voices"},
         "text": {"type": "string", "maxLength": 5000}},
        ["voice_id", "text"], synthesize, write=True),
    "list_voices": ActionDef("List available voices.",
        {}, [], list_voices),
}

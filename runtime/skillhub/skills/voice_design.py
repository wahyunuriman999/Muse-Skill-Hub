"""Voice design driver — real ElevenLabs voice design API.

Setup: an API key from https://elevenlabs.io/app/settings/api-keys.
Set ELEVENLABS_API_KEY (shared with the tts driver).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "voice-design"
REQUIRED_ENV = ["ELEVENLABS_API_KEY"]
SETUP_HELP = (
    "Sign up at https://elevenlabs.io, copy an API key from "
    "https://elevenlabs.io/app/settings/api-keys, and set ELEVENLABS_API_KEY."
)

_BASE = "https://api.elevenlabs.io"


def _headers() -> dict:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"xi-api-key": key, "Content-Type": "application/json"}


async def design_voice(params: dict) -> dict:
    r = await api_request(SKILL, "POST", f"{_BASE}/v2/voices/design",
                          headers=_headers(),
                          json={"voice_description": params["description"],
                                "text": params.get("preview_text",
                                                   "Hello, this is a preview of my new voice.")})
    previews = r.get("previews", [])
    return {"status": "ok", "generated_voice_id": r.get("generated_voice_id"),
            "preview_urls": [p.get("audio_base_64") is not None for p in previews],
            "note": "Use generated_voice_id with the tts skill to speak."}


ACTIONS = {
    "design_voice": ActionDef("Design a custom voice from a text description (needs confirm=true).",
        {"description": {"type": "string",
                         "description": "e.g. 'a warm female narrator, calm pace'"},
         "preview_text": {"type": "string"}},
        ["description"], design_voice, write=True),
}

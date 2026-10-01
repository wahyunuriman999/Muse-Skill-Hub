"""Podcast composer driver — multi-voice audio via ElevenLabs.

Composes a podcast episode/briefing from segments, each with its own voice,
synthesizes them with the tts driver backend, and returns the per-segment
audio (base64 MP3) plus the full script.

Setup: ELEVENLABS_API_KEY (shared with the tts driver).
"""
from __future__ import annotations

import base64
import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from . import tts as tts_driver

SKILL = "generate_podcast"
REQUIRED_ENV = ["ELEVENLABS_API_KEY"]
SETUP_HELP = (
    "Sign up at https://elevenlabs.io, copy an API key from "
    "https://elevenlabs.io/app/settings/api-keys, and set ELEVENLABS_API_KEY. "
    "Find voice IDs with the tts skill's list_voices action."
)


def _check() -> None:
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)


async def compose_episode(params: dict) -> dict:
    _check()
    segments = params["segments"][:20]
    parts = []
    script_lines = []
    for i, seg in enumerate(segments):
        audio = await tts_driver._synthesize_bytes(seg["voice_id"], seg["text"])
        parts.append({"index": i, "speaker": seg.get("speaker", f"voice_{i}"),
                      "voice_id": seg["voice_id"],
                      "audio_base64_mp3": base64.b64encode(audio).decode("ascii")})
        script_lines.append(f"[{seg.get('speaker', f'voice_{i}')}] {seg['text']}")
    return {"status": "ok", "title": params.get("title", "episode"),
            "segments": parts,
            "script": "\n\n".join(script_lines),
            "note": "Segments are in order; concatenate the MP3s to assemble the episode."}


ACTIONS = {
    "compose_episode": ActionDef("Synthesize a multi-voice episode (needs confirm=true).",
        {"title": {"type": "string"},
         "segments": {"type": "array", "maxItems": 20, "items": {
             "type": "object", "required": ["voice_id", "text"],
             "properties": {"speaker": {"type": "string"},
                            "voice_id": {"type": "string"},
                            "text": {"type": "string"}}}}},
        ["segments"], compose_episode, write=True),
}

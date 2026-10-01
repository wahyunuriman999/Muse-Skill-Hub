"""Spotify driver — real Spotify Web API implementation.

Setup: a user access token with scopes (user-read-playback-state, user-modify-playback-state,
playlist-read-private, user-read-recently-played). Get one via the Spotify console or your
own OAuth app at https://developer.spotify.com/dashboard. Set SPOTIFY_ACCESS_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "spotify"
REQUIRED_ENV = ["SPOTIFY_ACCESS_TOKEN"]
SETUP_HELP = (
    "Create an app at https://developer.spotify.com/dashboard, authorize a user with scopes "
    "user-read-playback-state, user-modify-playback-state, playlist-read-private, "
    "user-read-recently-played, and set SPOTIFY_ACCESS_TOKEN."
)

_BASE = "https://api.spotify.com/v1"


def _headers() -> dict:
    token = cred("SPOTIFY_ACCESS_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def search(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/search", headers=_headers(),
                          params={"q": params["query"],
                                  "type": params.get("type", "track,artist"),
                                  "limit": min(int(params.get("limit", 5)), 20)})
    out = {"status": "ok"}
    if "tracks" in r:
        out["tracks"] = [{"id": t["id"], "name": t["name"],
                          "artists": [a["name"] for a in t.get("artists", [])]}
                         for t in r["tracks"].get("items", [])]
    if "artists" in r:
        out["artists"] = [{"id": a["id"], "name": a["name"]} for a in r["artists"].get("items", [])]
    return out


async def get_playlists(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/me/playlists", headers=_headers(),
                          params={"limit": min(int(params.get("limit", 20)), 50)})
    return {"status": "ok", "playlists": [
        {"id": p["id"], "name": p["name"], "tracks": p.get("tracks", {}).get("total")}
        for p in r.get("items", [])]}


async def play(params: dict) -> dict:
    body = {}
    if params.get("context_uri"):
        body["context_uri"] = params["context_uri"]
    q = {"device_id": params["device_id"]} if params.get("device_id") else None
    await api_request(SKILL, "PUT", f"{_BASE}/me/player/play", headers=_headers(),
                      params=q, json=body)
    return {"status": "ok", "action": "play"}


async def pause(params: dict) -> dict:
    q = {"device_id": params["device_id"]} if params.get("device_id") else None
    await api_request(SKILL, "PUT", f"{_BASE}/me/player/pause", headers=_headers(), params=q)
    return {"status": "ok", "action": "pause"}


ACTIONS = {
    "search": ActionDef("Search tracks and artists.",
        {"query": {"type": "string"}, "type": {"type": "string", "default": "track,artist"},
         "limit": {"type": "integer", "default": 5, "maximum": 20}},
        ["query"], search),
    "get_playlists": ActionDef("List the user's playlists.",
        {"limit": {"type": "integer", "default": 20, "maximum": 50}},
        [], get_playlists),
    "play": ActionDef("Start/resume playback on an active device (needs confirm=true).",
        {"context_uri": {"type": "string", "description": "spotify:playlist:..., spotify:album:..."},
         "device_id": {"type": "string"}},
        [], play, write=True),
    "pause": ActionDef("Pause playback (needs confirm=true).",
        {"device_id": {"type": "string"}},
        [], pause, write=True),
}

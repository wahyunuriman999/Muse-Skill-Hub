"""Podcast search driver — real iTunes Search API (no key needed).

Searches Apple's podcast catalog: shows, episodes, artwork, feeds.
"""
from __future__ import annotations

from ..driver import ActionDef
from ..http import api_request

SKILL = "podcast"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — uses the public iTunes Search API."

_BASE = "https://itunes.apple.com/search"


async def search_podcasts(params: dict) -> dict:
    r = await api_request(SKILL, "GET", _BASE,
                          params={"term": params["query"], "media": "podcast",
                                  "entity": "podcast",
                                  "limit": min(int(params.get("limit", 10)), 50)})
    return {"status": "ok", "podcasts": [
        {"collectionId": p.get("collectionId"), "name": p.get("collectionName"),
         "artist": p.get("artistName"), "feedUrl": p.get("feedUrl"),
         "artwork": p.get("artworkUrl600")}
        for p in r.get("results", [])]}


async def search_episodes(params: dict) -> dict:
    r = await api_request(SKILL, "GET", _BASE,
                          params={"term": params["query"], "media": "podcast",
                                  "entity": "podcastEpisode",
                                  "limit": min(int(params.get("limit", 10)), 50)})
    return {"status": "ok", "episodes": [
        {"trackId": p.get("trackId"), "name": p.get("trackName"),
         "show": p.get("collectionName"), "released": p.get("releaseDate"),
         "duration_ms": p.get("trackTimeMillis"),
         "audio": p.get("episodeUrl")}
        for p in r.get("results", [])]}


ACTIONS = {
    "search_podcasts": ActionDef("Search podcast shows.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 10, "maximum": 50}},
        ["query"], search_podcasts),
    "search_episodes": ActionDef("Search podcast episodes (with audio URLs).",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 10, "maximum": 50}},
        ["query"], search_episodes),
}

"""Image search driver — real Serper.dev image search implementation.

Setup: an API key from https://serper.dev (free tier available). Set SERPER_API_KEY.
Returns direct image URLs plus source page links.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "image-search"
REQUIRED_ENV = ["SERPER_API_KEY"]
SETUP_HELP = (
    "Sign up at https://serper.dev, copy your API key from the dashboard, "
    "and set SERPER_API_KEY."
)

_BASE = "https://google.serper.dev/images"


def _headers() -> dict:
    key = cred("SERPER_API_KEY", SKILL)
    return {"X-API-KEY": key, "Content-Type": "application/json"}


async def search_images(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"q": params["query"],
                                "num": min(int(params.get("limit", 8)), 20)})
    return {"status": "ok", "images": [
        {"title": i.get("title"), "imageUrl": i.get("imageUrl"),
         "source": i.get("link"), "width": i.get("imageWidth"),
         "height": i.get("imageHeight")}
        for i in r.get("images", [])]}


ACTIONS = {
    "search_images": ActionDef("Search the web for images by text query.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 8, "maximum": 20}},
        ["query"], search_images),
}

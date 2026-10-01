"""Shopping driver — real Serper.dev shopping search implementation.

Setup: an API key from https://serper.dev. Set SERPER_API_KEY
(shared with the image-search driver).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "shopping"
REQUIRED_ENV = ["SERPER_API_KEY"]
SETUP_HELP = (
    "Sign up at https://serper.dev, copy your API key, and set SERPER_API_KEY."
)

_BASE = "https://google.serper.dev/shopping"


def _headers() -> dict:
    key = cred("SERPER_API_KEY", SKILL)
    return {"X-API-KEY": key, "Content-Type": "application/json"}


async def search_products(params: dict) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"q": params["query"],
                                "num": min(int(params.get("limit", 10)), 20)})
    return {"status": "ok", "products": [
        {"title": p.get("title"), "price": p.get("price"),
         "source": p.get("source"), "link": p.get("link"),
         "imageUrl": p.get("imageUrl"), "rating": p.get("rating")}
        for p in r.get("shopping", [])]}


ACTIONS = {
    "search_products": ActionDef("Search products with prices across merchants.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 10, "maximum": 20}},
        ["query"], search_products),
}

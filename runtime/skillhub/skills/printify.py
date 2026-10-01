"""Printify driver — real Printify API implementation.

Setup: a Personal Access Token from https://printify.com/app/account/api.
Set PRINTIFY_API_TOKEN.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "printify"
REQUIRED_ENV = ["PRINTIFY_API_TOKEN"]
SETUP_HELP = (
    "Go to https://printify.com/app/account/api, generate a Personal Access Token, "
    "and set PRINTIFY_API_TOKEN."
)

_BASE = "https://api.printify.com/v1"


def _headers() -> dict:
    token = cred("PRINTIFY_API_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def list_shops(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/shops.json", headers=_headers())
    return {"status": "ok", "shops": [
        {"id": s.get("id"), "title": s.get("title")} for s in (r or [])]}


async def list_products(params: dict) -> dict:
    r = await api_request(SKILL, "GET", f"{_BASE}/shops/{params['shop_id']}/products.json",
                          headers=_headers(),
                          params={"limit": min(int(params.get("limit", 20)), 100)})
    items = r.get("data", []) if isinstance(r, dict) else []
    return {"status": "ok", "products": [
        {"id": p.get("id"), "title": p.get("title"),
         "is_locked": p.get("is_locked")} for p in items]}


ACTIONS = {
    "list_shops": ActionDef("List Printify shops.", {}, [], list_shops),
    "list_products": ActionDef("List products in a shop.",
        {"shop_id": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        ["shop_id"], list_products),
}

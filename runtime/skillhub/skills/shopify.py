"""Shopify driver — real Shopify Admin REST API implementation.

Setup: in Shopify admin create a custom app with Admin API access token.
Set SHOPIFY_STORE (e.g. my-shop) and SHOPIFY_ADMIN_TOKEN (shpat_...).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "shopify"
REQUIRED_ENV = ["SHOPIFY_STORE", "SHOPIFY_ADMIN_TOKEN"]
SETUP_HELP = ("In Shopify admin: Settings > Apps > Develop apps > create app with "
              "read_products/read_orders scopes, then copy the Admin API access token.")


def _base() -> tuple[str, dict]:
    store = os.environ.get("SHOPIFY_STORE")
    token = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    if not store or not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return (f"https://{store}.myshopify.com/admin/api/2024-10",
            {"X-Shopify-Access-Token": token, "Content-Type": "application/json"})


async def list_products(params: dict) -> dict:
    base, headers = _base()
    r = await api_request(SKILL, "GET", f"{base}/products.json",
                          headers=headers, params={"limit": 10})
    return {"status": "ok", "products": [
        {"id": p["id"], "title": p.get("title"), "status": p.get("status")}
        for p in r.get("products", [])]}


async def list_orders(params: dict) -> dict:
    base, headers = _base()
    r = await api_request(SKILL, "GET", f"{base}/orders.json",
                          headers=headers, params={"limit": 10, "status": "any"})
    return {"status": "ok", "orders": [
        {"id": o["id"], "name": o.get("name"),
         "total": o.get("total_price"), "currency": o.get("currency")}
        for o in r.get("orders", [])]}


ACTIONS = {
    "list_products": ActionDef("List store products.", {}, [], list_products),
    "list_orders": ActionDef("List recent orders.", {}, [], list_orders),
}

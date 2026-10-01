"""Stripe driver — real Stripe REST API implementation.

Setup: copy your secret key from the Stripe dashboard, set STRIPE_SECRET_KEY.
Use test-mode keys (sk_test_...) for safe experimentation.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "stripe"
REQUIRED_ENV = ["STRIPE_SECRET_KEY"]
SETUP_HELP = "Copy the secret key from https://dashboard.stripe.com/apikeys (use sk_test_... for testing)."

_BASE = "https://api.stripe.com/v1"


def _auth() -> tuple[dict, str]:
    key = cred("STRIPE_SECRET_KEY", SKILL)
    return ({}, key)


async def _req(method: str, path: str, data: dict | None = None) -> dict:
    headers, key = _auth()
    import base64
    headers["Authorization"] = "Basic " + base64.b64encode(f"{key}:".encode()).decode()
    return await api_request(SKILL, method, f"{_BASE}{path}", headers=headers, data=data)


async def list_customers(params: dict) -> dict:
    r = await _req("GET", "/customers?limit=10")
    return {"status": "ok", "customers": [
        {"id": c["id"], "email": c.get("email"), "name": c.get("name")}
        for c in r.get("data", [])]}


async def list_invoices(params: dict) -> dict:
    r = await _req("GET", "/invoices?limit=10")
    return {"status": "ok", "invoices": [
        {"id": i["id"], "amount_due": i.get("amount_due"), "currency": i.get("currency"),
         "status": i.get("status")} for i in r.get("data", [])]}


async def create_payment_link(params: dict) -> dict:
    data = {
        "line_items[0][price_data][currency]": params.get("currency", "usd"),
        "line_items[0][price_data][unit_amount]": str(int(params["amount_cents"])),
        "line_items[0][price_data][product_data][name]": params["product_name"],
        "line_items[0][quantity]": "1",
    }
    r = await _req("POST", "/payment_links", data=data)
    return {"status": "ok", "url": r.get("url"), "id": r.get("id")}


ACTIONS = {
    "list_customers": ActionDef("List Stripe customers.", {}, [], list_customers),
    "list_invoices": ActionDef("List recent invoices.", {}, [], list_invoices),
    "create_payment_link": ActionDef(
        "Create a Stripe payment link (needs confirm=true).",
        {"product_name": {"type": "string"}, "amount_cents": {"type": "integer"},
         "currency": {"type": "string", "default": "usd"}},
        ["product_name", "amount_cents"], create_payment_link, write=True),
}

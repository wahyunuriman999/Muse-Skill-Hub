"""Plaid driver — real Plaid API implementation (Sandbox).

Setup: client_id + secret from https://dashboard.plaid.com (free sandbox).
This driver runs the Sandbox flow end-to-end: it creates a sandbox Item,
exchanges the public token, and reads accounts/balances — no bank login needed.
Set PLAID_CLIENT_ID and PLAID_SECRET.
"""
from __future__ import annotations


from ..credentials import cred
from ..driver import ActionDef
from ..http import api_request

SKILL = "plaid"
REQUIRED_ENV = ["PLAID_CLIENT_ID", "PLAID_SECRET"]
SETUP_HELP = (
    "Sign up at https://dashboard.plaid.com, copy the Sandbox client_id and secret, "
    "and set PLAID_CLIENT_ID and PLAID_SECRET. For production Items, switch _BASE "
    "to https://production.plaid.com and complete Plaid Link separately."
)

_BASE = "https://sandbox.plaid.com"


def _creds() -> tuple[str, str]:
    return cred("PLAID_CLIENT_ID", SKILL), cred("PLAID_SECRET", SKILL)


async def sandbox_connect(params: dict) -> dict:
    """Create a sandbox Item and return its access token (needs confirm=true)."""
    cid, sec = _creds()
    r = await api_request(SKILL, "POST", f"{_BASE}/sandbox/public/token/create",
                          json={"client_id": cid, "secret": sec,
                                "institution_id": params.get("institution_id", "ins_109508"),
                                "initial_products": ["transactions"]})
    pub = r["public_token"]
    r2 = await api_request(SKILL, "POST", f"{_BASE}/item/public/token/exchange",
                           json={"client_id": cid, "secret": sec,
                                 "public_token": pub})
    return {"status": "ok", "access_token": r2["access_token"],
            "item_id": r2["item_id"],
            "note": "Sandbox access token — store it and pass to get_balances."}


async def get_balances(params: dict) -> dict:
    cid, sec = _creds()
    r = await api_request(SKILL, "POST", f"{_BASE}/accounts/balance/get",
                          json={"client_id": cid, "secret": sec,
                                "access_token": params["access_token"]})
    return {"status": "ok", "accounts": [
        {"account_id": a.get("account_id"), "name": a.get("name"),
         "type": a.get("type"), "balances": a.get("balances")}
        for a in r.get("accounts", [])]}


ACTIONS = {
    "sandbox_connect": ActionDef("Create a Plaid Sandbox item and get an access token (needs confirm=true).",
        {"institution_id": {"type": "string", "default": "ins_109508",
                            "description": "Sandbox institution, e.g. ins_109508 (First Platypus Bank)"}},
        [], sandbox_connect, write=True),
    "get_balances": ActionDef("Read accounts and balances for an access token.",
        {"access_token": {"type": "string"}},
        ["access_token"], get_balances),
}

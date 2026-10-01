"""Wallet — LOCAL payment-records reference implementation.

Tracks wallet connection state and saved payment-method *records* (labels only —
never full card numbers) in a local JSON store. Reference implementation of the
wallet interface; real charging requires a payment provider integration.
Swap the backend for production use.
"""
from __future__ import annotations

import time

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "wallet"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE + " Only non-sensitive labels are stored; never full card numbers."

_STORE = "wallet"


def _load() -> dict:
    return read_json(_STORE, {"connected": False, "provider": None, "methods": []})


async def get_state(params: dict) -> dict:
    w = _load()
    return {"status": "ok", "connected": w["connected"], "provider": w["provider"],
            "method_count": len(w["methods"])}


async def connect(params: dict) -> dict:
    w = _load()
    w["connected"] = True
    w["provider"] = params.get("provider", "manual")
    w["connected_at"] = int(time.time())
    write_json(_STORE, w)
    return {"status": "ok", "connected": True, "provider": w["provider"]}


async def add_payment_method(params: dict) -> dict:
    w = _load()
    method = {"id": f"pm_{int(time.time())}", "label": params["label"],
              "brand": params.get("brand", ""), "last4": params.get("last4", ""),
              "added_at": int(time.time())}
    w["methods"].append(method)
    write_json(_STORE, w)
    return {"status": "ok", "method": method,
            "note": "Label-only record; no sensitive card data is stored."}


async def list_payment_methods(params: dict) -> dict:
    return {"status": "ok", "methods": _load()["methods"]}


ACTIONS = {
    "get_state": ActionDef("Check wallet connection state.", {}, [], get_state),
    "connect": ActionDef("Mark a wallet provider as connected (needs confirm=true).",
        {"provider": {"type": "string", "default": "manual"}},
        [], connect, write=True),
    "add_payment_method": ActionDef("Save a payment-method label record (needs confirm=true).",
        {"label": {"type": "string", "description": "e.g. 'BCA debit'"},
         "brand": {"type": "string"}, "last4": {"type": "string"}},
        ["label"], add_payment_method, write=True),
    "list_payment_methods": ActionDef("List saved payment-method records.",
        {}, [], list_payment_methods),
}

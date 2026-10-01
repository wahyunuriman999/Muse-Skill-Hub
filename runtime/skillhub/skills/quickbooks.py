"""QuickBooks driver — real QuickBooks Online Accounting API implementation.

Setup: an OAuth2 access token for your QuickBooks company (complete the OAuth
flow from your Intuit developer app at https://developer.intuit.com).
Set QUICKBOOKS_ACCESS_TOKEN and QUICKBOOKS_REALM_ID (company ID).
"""
from __future__ import annotations

import os
import urllib.parse

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "quickbooks"
REQUIRED_ENV = ["QUICKBOOKS_ACCESS_TOKEN", "QUICKBOOKS_REALM_ID"]
SETUP_HELP = (
    "Create an app at https://developer.intuit.com, complete OAuth2 for your "
    "QuickBooks company, and set QUICKBOOKS_ACCESS_TOKEN and QUICKBOOKS_REALM_ID."
)

_BASE = "https://quickbooks.api.intuit.com/v3/company"


def _ctx() -> tuple[dict, str]:
    token = os.environ.get("QUICKBOOKS_ACCESS_TOKEN")
    realm = os.environ.get("QUICKBOOKS_REALM_ID")
    if not token or not realm:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Accept": "application/json",
            "Content-Type": "application/json"}, realm


async def list_customers(params: dict) -> dict:
    headers, realm = _ctx()
    q = urllib.parse.quote("select * from Customer maxresults "
                           f"{min(int(params.get('limit', 20)), 100)}")
    r = await api_request(SKILL, "GET", f"{_BASE}/{realm}/query",
                          headers=headers, params={"query": q, "minorversion": "75"})
    customers = ((r.get("QueryResponse") or {}).get("Customer")) or []
    return {"status": "ok", "customers": [
        {"id": c.get("Id"), "name": c.get("DisplayName"),
         "email": (c.get("PrimaryEmailAddr") or {}).get("Address")}
        for c in customers]}


async def run_query(params: dict) -> dict:
    headers, realm = _ctx()
    q = urllib.parse.quote(params["query"])
    r = await api_request(SKILL, "GET", f"{_BASE}/{realm}/query",
                          headers=headers, params={"query": q, "minorversion": "75"})
    return {"status": "ok", "response": r.get("QueryResponse", {})}


ACTIONS = {
    "list_customers": ActionDef("List QuickBooks customers.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_customers),
    "run_query": ActionDef("Run a read-only QuickBooks entity query, e.g. 'select * from Invoice'.",
        {"query": {"type": "string"}},
        ["query"], run_query),
}

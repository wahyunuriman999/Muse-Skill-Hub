"""Voice calls driver — real Twilio Programmable Voice implementation.

Setup: Account SID + Auth Token from https://console.twilio.com.
Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN. Outbound calls also need a
Twilio phone number (TWILIO_FROM_NUMBER) and TwiML instructions URL.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "voice-calls"
REQUIRED_ENV = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
SETUP_HELP = (
    "Copy the Account SID and Auth Token from https://console.twilio.com and set "
    "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN. For outbound calls also set "
    "TWILIO_FROM_NUMBER (your Twilio number)."
)


def _ctx():
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return sid, (sid, token)


async def list_calls(params: dict) -> dict:
    import base64
    sid, auth = _ctx()
    basic = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    r = await api_request(SKILL, "GET",
                          f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
                          headers={"Authorization": f"Basic {basic}"},
                          params={"PageSize": min(int(params.get("limit", 20)), 100)})
    return {"status": "ok", "calls": [
        {"sid": c.get("sid"), "from": c.get("from"), "to": c.get("to"),
         "status": c.get("status"), "duration": c.get("duration")}
        for c in r.get("calls", [])]}


async def make_call(params: dict) -> dict:
    import base64
    sid, auth = _ctx()
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    if not from_number:
        raise CredentialsMissing(SKILL, ["TWILIO_FROM_NUMBER"],
                                 "Set TWILIO_FROM_NUMBER to your Twilio phone number.")
    basic = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    r = await api_request(SKILL, "POST",
                          f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json",
                          headers={"Authorization": f"Basic {basic}"},
                          data={"From": from_number, "To": params["to"],
                                "Url": params["twiml_url"]})
    return {"status": "ok", "call_sid": r.get("sid"), "state": r.get("status")}


ACTIONS = {
    "list_calls": ActionDef("List recent calls.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_calls),
    "make_call": ActionDef("Place an outbound call — real telephony charges apply (needs confirm=true).",
        {"to": {"type": "string", "description": "E.164 number, e.g. +62812..."},
         "twiml_url": {"type": "string", "description": "URL serving TwiML instructions"}},
        ["to", "twiml_url"], make_call, write=True),
}

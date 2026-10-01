"""Outlook Calendar driver — real Microsoft Graph implementation.

Setup: an OAuth2 access token with Calendars.ReadWrite. Register an app at
https://portal.azure.com (Microsoft Entra) or use the Graph Explorer to mint a
token for testing. Set MICROSOFT_ACCESS_TOKEN (shared with outlook-mail/contacts).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "outlook-calendar"
REQUIRED_ENV = ["MICROSOFT_ACCESS_TOKEN"]
SETUP_HELP = (
    "Register an app at https://portal.azure.com with Calendars.ReadWrite (delegated), "
    "complete OAuth, and set MICROSOFT_ACCESS_TOKEN. For quick testing, mint one in "
    "https://developer.microsoft.com/graph/graph-explorer."
)

_BASE = "https://graph.microsoft.com/v1.0/me/calendar"


def _headers() -> dict:
    token = cred("MICROSOFT_ACCESS_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(e: dict) -> dict:
    return {"id": e.get("id"), "subject": e.get("subject"),
            "start": (e.get("start") or {}).get("dateTime"),
            "end": (e.get("end") or {}).get("dateTime"),
            "location": ((e.get("location") or {}).get("displayName"))}


async def list_events(params: dict) -> dict:
    q = {"$top": min(int(params.get("limit", 20)), 100),
         "$orderby": "start/dateTime"}
    if params.get("start"):
        q["$filter"] = f"start/dateTime ge '{params['start']}'"
    r = await api_request(SKILL, "GET", f"{_BASE}/events",
                          headers=_headers(), params=q)
    return {"status": "ok", "events": [_fmt(e) for e in r.get("value", [])]}


async def create_event(params: dict) -> dict:
    body = {"subject": params["subject"],
            "start": {"dateTime": params["start"], "timeZone": params.get("timezone", "UTC")},
            "end": {"dateTime": params["end"], "timeZone": params.get("timezone", "UTC")}}
    if params.get("body"):
        body["body"] = {"contentType": "Text", "content": params["body"]}
    r = await api_request(SKILL, "POST", f"{_BASE}/events",
                          headers=_headers(), json=body)
    return {"status": "ok", "event": _fmt(r)}


async def delete_event(params: dict) -> dict:
    await api_request(SKILL, "DELETE", f"{_BASE}/events/{params['event_id']}",
                      headers=_headers())
    return {"status": "ok", "deleted": params["event_id"]}


ACTIONS = {
    "list_events": ActionDef("List Outlook calendar events.",
        {"start": {"type": "string", "description": "ISO8601 lower bound filter"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_events, required_scopes=["Calendars.Read"]),
    "create_event": ActionDef("Create an event (needs confirm=true).",
        {"subject": {"type": "string"}, "start": {"type": "string"},
         "end": {"type": "string"}, "timezone": {"type": "string", "default": "UTC"},
         "body": {"type": "string"}},
        ["subject", "start", "end"], create_event, write=True, required_scopes=["Calendars.ReadWrite"]),
    "delete_event": ActionDef("Delete an event (needs confirm=true).",
        {"event_id": {"type": "string"}}, ["event_id"], delete_event, write=True, required_scopes=["Calendars.ReadWrite"]),
}

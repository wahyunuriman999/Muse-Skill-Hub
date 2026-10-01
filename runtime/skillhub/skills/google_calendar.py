"""Google Calendar driver — real Calendar API v3 implementation.

Setup: an OAuth2 access token with Calendar scopes (calendar, calendar.events).
Get one via the Google OAuth Playground:
https://developers.google.com/oauthplayground (select Calendar API scopes).
Set GOOGLE_OAUTH_TOKEN (shared with the gmail/sheets/drive drivers).
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "google-calendar"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Calendar API scopes "
    "(calendar, calendar.events), authorize, and set the access token as GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://www.googleapis.com/calendar/v3/calendars/primary"


def _headers() -> dict:
    token = os.environ.get("GOOGLE_OAUTH_TOKEN")
    if not token:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _fmt(event: dict) -> dict:
    start = event.get("start", {})
    end = event.get("end", {})
    return {"id": event.get("id"), "summary": event.get("summary"),
            "start": start.get("dateTime") or start.get("date"),
            "end": end.get("dateTime") or end.get("date"),
            "location": event.get("location"),
            "htmlLink": event.get("htmlLink")}


async def list_events(params: dict) -> dict:
    q = {"singleEvents": "true", "orderBy": "startTime",
         "maxResults": min(int(params.get("limit", 10)), 100)}
    if params.get("time_min"):
        q["timeMin"] = params["time_min"]
    if params.get("time_max"):
        q["timeMax"] = params["time_max"]
    if params.get("query"):
        q["q"] = params["query"]
    r = await api_request(SKILL, "GET", f"{_BASE}/events", headers=_headers(), params=q)
    return {"status": "ok", "events": [_fmt(e) for e in r.get("items", [])]}


async def create_event(params: dict) -> dict:
    body = {"summary": params["summary"], "start": {"dateTime": params["start"]},
            "end": {"dateTime": params["end"]}}
    if params.get("description"):
        body["description"] = params["description"]
    if params.get("location"):
        body["location"] = params["location"]
    r = await api_request(SKILL, "POST", f"{_BASE}/events", headers=_headers(), json=body)
    return {"status": "ok", "event": _fmt(r)}


ACTIONS = {
    "list_events": ActionDef("List upcoming events on the primary calendar.",
        {"time_min": {"type": "string", "description": "RFC3339 lower bound, e.g. 2026-10-01T00:00:00+07:00"},
         "time_max": {"type": "string", "description": "RFC3339 upper bound"},
         "query": {"type": "string", "description": "Free-text search"},
         "limit": {"type": "integer", "default": 10, "maximum": 100}},
        [], list_events),
    "create_event": ActionDef("Create an event (needs confirm=true). Times are RFC3339 with offset.",
        {"summary": {"type": "string"},
         "start": {"type": "string", "description": "e.g. 2026-10-02T09:00:00+07:00"},
         "end": {"type": "string"},
         "description": {"type": "string"}, "location": {"type": "string"}},
        ["summary", "start", "end"], create_event, write=True),
}

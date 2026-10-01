"""Google Sheets driver — real Sheets API v4 implementation (read + append).

Setup: an OAuth2 access token with Sheets scopes (spreadsheets).
Get one via the Google OAuth Playground:
https://developers.google.com/oauthplayground (select Sheets API scopes).
Set GOOGLE_OAUTH_TOKEN (shared with the gmail/calendar/drive drivers).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "google-sheets"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Sheets API scopes "
    "(spreadsheets), authorize, and set the access token as GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


def _headers() -> dict:
    token = cred("GOOGLE_OAUTH_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def read_range(params: dict) -> dict:
    r = await api_request(SKILL, "GET",
                          f"{_BASE}/{params['spreadsheet_id']}/values/{params['range']}",
                          headers=_headers())
    return {"status": "ok", "range": r.get("range"), "values": r.get("values", [])}


async def append_row(params: dict) -> dict:
    r = await api_request(SKILL, "POST",
                          f"{_BASE}/{params['spreadsheet_id']}/values/{params['range']}:append",
                          headers=_headers(),
                          params={"valueInputOption": "USER_ENTERED"},
                          json={"values": [params["values"]]})
    return {"status": "ok", "updatedRange": r.get("updates", {}).get("updatedRange"),
            "updatedRows": r.get("updates", {}).get("updatedRows")}


ACTIONS = {
    "read_range": ActionDef("Read values from a range, e.g. 'Sheet1!A1:D20'.",
        {"spreadsheet_id": {"type": "string", "description": "The spreadsheet ID from its URL"},
         "range": {"type": "string", "description": "A1 notation range"}},
        ["spreadsheet_id", "range"], read_range, required_scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]),
    "append_row": ActionDef("Append one row to a range (needs confirm=true).",
        {"spreadsheet_id": {"type": "string"}, "range": {"type": "string"},
         "values": {"type": "array", "items": {"type": "string"},
                    "description": "Row values left to right"}},
        ["spreadsheet_id", "range", "values"], append_row, write=True, required_scopes=["https://www.googleapis.com/auth/spreadsheets"]),
}

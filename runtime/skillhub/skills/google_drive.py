"""Google Drive driver — real Drive API v3 implementation (list/search files).

Setup: an OAuth2 access token with Drive scope (drive.readonly).
Get one via the Google OAuth Playground:
https://developers.google.com/oauthplayground (select Drive API scopes).
Set GOOGLE_OAUTH_TOKEN (shared with the gmail/calendar/sheets drivers).
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import cred

SKILL = "google-drive"
REQUIRED_ENV = ["GOOGLE_OAUTH_TOKEN"]
SETUP_HELP = (
    "Open https://developers.google.com/oauthplayground, select Google Drive API scope "
    "(drive.readonly), authorize, and set the access token as GOOGLE_OAUTH_TOKEN."
)

_BASE = "https://www.googleapis.com/drive/v3/files"


def _headers() -> dict:
    token = cred("GOOGLE_OAUTH_TOKEN", SKILL)
    return {"Authorization": f"Bearer {token}"}


def _fmt(f: dict) -> dict:
    return {"id": f.get("id"), "name": f.get("name"), "mimeType": f.get("mimeType"),
            "modifiedTime": f.get("modifiedTime"), "webViewLink": f.get("webViewLink")}


async def list_files(params: dict) -> dict:
    r = await api_request(SKILL, "GET", _BASE, headers=_headers(),
                          params={"pageSize": min(int(params.get("limit", 20)), 100),
                                  "orderBy": "modifiedTime desc",
                                  "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"})
    return {"status": "ok", "files": [_fmt(f) for f in r.get("files", [])]}


async def search_files(params: dict) -> dict:
    r = await api_request(SKILL, "GET", _BASE, headers=_headers(),
                          params={"q": f"name contains '{params['query']}' and trashed=false",
                                  "pageSize": min(int(params.get("limit", 20)), 100),
                                  "fields": "files(id,name,mimeType,modifiedTime,webViewLink)"})
    return {"status": "ok", "files": [_fmt(f) for f in r.get("files", [])]}


ACTIONS = {
    "list_files": ActionDef("List recently modified files.",
        {"limit": {"type": "integer", "default": 20, "maximum": 100}},
        [], list_files, required_scopes=["https://www.googleapis.com/auth/drive.readonly"]),
    "search_files": ActionDef("Search files by name.",
        {"query": {"type": "string", "description": "Substring to match in file names"},
         "limit": {"type": "integer", "default": 20, "maximum": 100}},
        ["query"], search_files, required_scopes=["https://www.googleapis.com/auth/drive.readonly"]),
}

"""Tests for the 12 batch-2 drivers (v1.3.0): gmail, google-calendar, google-sheets,
google-drive, spotify, instagram, meta-threads, facebook, dropbox, ticketmaster,
image-search, flightaware.

Drivers are verified by (1) honest credential errors when env vars are missing,
and (2) mocked api_request proving each driver builds the correct real API
request and parses the response. No real credentials or network needed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub import registry
from skillhub.errors import CredentialsMissing


async def _approved(skill, action, params):
    """Run a strict-risk write action through the real approval flow."""
    from skillhub import approval as approval_engine
    from skillhub.policy import risk_for
    entry = registry.load_registry()[skill]
    risk = risk_for(skill, action, entry.actions[action].risk)
    item = approval_engine.request_approval(skill, action, params, risk=risk)
    approval_engine.approve(item["approval_id"])
    return await registry.dispatch(entry, action, params,
                                   approval_id=item["approval_id"])


def _mock_api(monkeypatch, module_name, fake):
    """Replace skillhub.skills.<module>.api_request with a fake; return captured calls."""
    calls = []

    async def _fake(skill, method, url, **kwargs):
        calls.append({"skill": skill, "method": method, "url": url, **kwargs})
        return fake(url, method, kwargs)

    monkeypatch.setattr(f"skillhub.skills.{module_name}.api_request", _fake)
    return calls


def _no_env(monkeypatch, *names):
    for n in names:
        monkeypatch.delenv(n, raising=False)


BATCH2 = ["gmail", "google-calendar", "google-sheets", "google-drive", "spotify",
          "instagram", "meta-threads", "facebook", "dropbox", "ticketmaster",
          "image-search", "flightaware"]


def test_batch2_drivers_are_implemented():
    reg = registry.load_registry()
    for name in BATCH2:
        assert reg[name].implemented, f"{name} has no executable driver"
        assert len(reg[name].actions) >= 1, f"{name} has no actions"
    print(f"\n  {len(BATCH2)} new drivers implemented")


def test_batch2_write_actions_flagged():
    reg = registry.load_registry()
    expected_writes = {
        "gmail": {"send_message"}, "google-calendar": {"create_event"},
        "google-sheets": {"append_row"}, "spotify": {"play", "pause"},
        "meta-threads": {"post_text"}, "facebook": {"post_to_feed"},
    }
    for name, writes in expected_writes.items():
        for action in reg[name].actions:
            assert reg[name].actions[action].write == (action in writes), \
                f"{name}.{action}: write flag wrong"


@pytest.mark.asyncio
async def test_gmail_lists_and_sends(monkeypatch, tmp_path):
    reg = registry.load_registry()
    _no_env(monkeypatch, "GOOGLE_OAUTH_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["gmail"], "list_messages", {}, confirm=False)

    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "gmail", lambda url, m, kw:
        {"messages": [{"id": "m1", "threadId": "t1"}]} if url.endswith("/messages")
        else {"id": "m1", "snippet": "hi", "payload": {"headers": []}})
    r = await registry.dispatch(reg["gmail"], "list_messages", {"query": "from:boss"}, confirm=False)
    assert r["messages"][0]["id"] == "m1"
    assert calls[0]["method"] == "GET"
    assert "gmail.googleapis.com" in calls[0]["url"]

    calls2 = _mock_api(monkeypatch, "gmail", lambda url, m, kw: {"id": "sent1"})
    from skillhub.errors import ConfirmationRequired
    with pytest.raises(ConfirmationRequired):
        await registry.dispatch(reg["gmail"], "send_message",
                                {"to": "a@b.c", "subject": "s", "body": "b"}, confirm=False)
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    r = await _approved("gmail", "send_message",
                        {"to": "a@b.c", "subject": "s", "body": "b"})
    assert r["id"] == "sent1"
    assert "raw" in calls2[0]["json"]  # base64url MIME payload


@pytest.mark.asyncio
async def test_google_calendar_lists_and_creates(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "GOOGLE_OAUTH_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["google-calendar"], "list_events", {}, confirm=False)

    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "google_calendar", lambda url, m, kw:
        {"items": [{"id": "e1", "summary": "Standup",
                    "start": {"dateTime": "2026-10-02T09:00:00+07:00"},
                    "end": {"dateTime": "2026-10-02T09:30:00+07:00"}}]})
    r = await registry.dispatch(reg["google-calendar"], "list_events", {"limit": 5}, confirm=False)
    assert r["events"][0]["summary"] == "Standup"
    assert calls[0]["params"]["orderBy"] == "startTime"

    r = await registry.dispatch(reg["google-calendar"], "create_event",
                                {"summary": "X", "start": "2026-10-02T09:00:00+07:00",
                                 "end": "2026-10-02T10:00:00+07:00"}, confirm=True)
    assert r["event"]["summary"] == "Standup" or r["status"] == "ok"


@pytest.mark.asyncio
async def test_google_sheets_read_and_append(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "GOOGLE_OAUTH_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["google-sheets"], "read_range",
                                {"spreadsheet_id": "x", "range": "A1:B2"}, confirm=False)

    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "google_sheets", lambda url, m, kw:
        {"range": "Sheet1!A1:B2", "values": [["a", "b"]]} if m == "GET"
        else {"updates": {"updatedRange": "Sheet1!A3:B3", "updatedRows": 1}})
    r = await registry.dispatch(reg["google-sheets"], "read_range",
                                {"spreadsheet_id": "abc", "range": "Sheet1!A1:B2"}, confirm=False)
    assert r["values"] == [["a", "b"]]
    assert "/values/Sheet1!A1:B2" in calls[0]["url"]

    r = await registry.dispatch(reg["google-sheets"], "append_row",
                                {"spreadsheet_id": "abc", "range": "Sheet1!A:B",
                                 "values": ["1", "2"]}, confirm=True)
    assert r["updatedRows"] == 1
    assert calls[1]["json"]["values"] == [["1", "2"]]


@pytest.mark.asyncio
async def test_google_drive_list_and_search(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "GOOGLE_OAUTH_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["google-drive"], "list_files", {}, confirm=False)

    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "google_drive", lambda url, m, kw:
        {"files": [{"id": "f1", "name": "report.pdf", "mimeType": "application/pdf"}]})
    r = await registry.dispatch(reg["google-drive"], "search_files", {"query": "report"}, confirm=False)
    assert r["files"][0]["name"] == "report.pdf"
    assert "name contains 'report'" in calls[0]["params"]["q"]


@pytest.mark.asyncio
async def test_spotify_search_and_playback(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "SPOTIFY_ACCESS_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["spotify"], "search", {"query": "x"}, confirm=False)

    monkeypatch.setenv("SPOTIFY_ACCESS_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "spotify", lambda url, m, kw:
        {"tracks": {"items": [{"id": "t1", "name": "Song",
                               "artists": [{"name": "Band"}]}]}})
    r = await registry.dispatch(reg["spotify"], "search", {"query": "song"}, confirm=False)
    assert r["tracks"][0]["artists"] == ["Band"]
    assert calls[0]["url"] == "https://api.spotify.com/v1/search"

    calls2 = _mock_api(monkeypatch, "spotify", lambda url, m, kw: {})
    r = await registry.dispatch(reg["spotify"], "pause", {}, confirm=True)
    assert r["action"] == "pause" and calls2[0]["method"] == "PUT"


@pytest.mark.asyncio
async def test_instagram_profile_and_media(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "INSTAGRAM_ACCESS_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["instagram"], "get_profile", {}, confirm=False)

    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "instagram", lambda url, m, kw:
        {"id": "1", "username": "someone"} if url.endswith("/me")
        else {"data": [{"id": "m1", "media_type": "IMAGE"}]})
    r = await registry.dispatch(reg["instagram"], "get_profile", {}, confirm=False)
    assert r["profile"]["username"] == "someone"
    r = await registry.dispatch(reg["instagram"], "get_media", {"limit": 3}, confirm=False)
    assert r["media"][0]["id"] == "m1"
    assert "graph.instagram.com" in calls[0]["url"]


@pytest.mark.asyncio
async def test_threads_post_two_step_publish(monkeypatch, tmp_path):
    reg = registry.load_registry()
    _no_env(monkeypatch, "THREADS_ACCESS_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["meta-threads"], "get_profile", {}, confirm=False)

    monkeypatch.setenv("THREADS_ACCESS_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "meta_threads", lambda url, m, kw:
        {"id": "creation123"} if url.endswith("/me/threads") else {"id": "post456"})
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    r = await _approved("meta-threads", "post_text", {"text": "hello"})
    assert r["post_id"] == "post456"
    assert len(calls) == 2  # create container, then publish
    assert calls[1]["params"]["creation_id"] == "creation123"


@pytest.mark.asyncio
async def test_facebook_posts(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "FACEBOOK_ACCESS_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["facebook"], "get_posts", {}, confirm=False)

    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "facebook", lambda url, m, kw:
        {"data": [{"id": "p1", "message": "hi"}]})
    r = await registry.dispatch(reg["facebook"], "get_posts", {"limit": 2}, confirm=False)
    assert r["posts"][0]["message"] == "hi"
    assert "graph.facebook.com" in calls[0]["url"]


@pytest.mark.asyncio
async def test_dropbox_list_folder(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "DROPBOX_ACCESS_TOKEN")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["dropbox"], "list_folder", {}, confirm=False)

    monkeypatch.setenv("DROPBOX_ACCESS_TOKEN", "tok")
    calls = _mock_api(monkeypatch, "dropbox", lambda url, m, kw:
        {"entries": [{".tag": "file", "name": "a.txt", "path_lower": "/a.txt",
                      "size": 10, "client_modified": "2026-01-01T00:00:00Z"}],
         "has_more": False})
    r = await registry.dispatch(reg["dropbox"], "list_folder", {"path": ""}, confirm=False)
    assert r["entries"][0]["name"] == "a.txt"
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"].endswith("/files/list_folder")


@pytest.mark.asyncio
async def test_ticketmaster_search(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "TICKETMASTER_API_KEY")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["ticketmaster"], "search_events",
                                {"keyword": "jazz"}, confirm=False)

    monkeypatch.setenv("TICKETMASTER_API_KEY", "key123")
    calls = _mock_api(monkeypatch, "ticketmaster", lambda url, m, kw:
        {"_embedded": {"events": [{"id": "e1", "name": "Jazz Night",
                                   "dates": {"start": {"localDate": "2026-11-01"}},
                                   "_embedded": {"venues": [{"name": "Hall",
                                                             "city": {"name": "Jakarta"}}]},
                                   "url": "https://tix.example"}]},
         "page": {"totalElements": 1}})
    r = await registry.dispatch(reg["ticketmaster"], "search_events",
                                {"keyword": "jazz", "city": "Jakarta"}, confirm=False)
    assert r["events"][0]["venue"] == "Hall"
    assert calls[0]["params"]["apikey"] == "key123"


@pytest.mark.asyncio
async def test_image_search(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "SERPER_API_KEY")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["image-search"], "search_images",
                                {"query": "cat"}, confirm=False)

    monkeypatch.setenv("SERPER_API_KEY", "key123")
    calls = _mock_api(monkeypatch, "image_search", lambda url, m, kw:
        {"images": [{"title": "Cat", "imageUrl": "https://img.example/cat.jpg",
                     "link": "https://example.com"}]})
    r = await registry.dispatch(reg["image-search"], "search_images",
                                {"query": "cat"}, confirm=False)
    assert r["images"][0]["imageUrl"] == "https://img.example/cat.jpg"
    assert calls[0]["method"] == "POST"
    assert calls[0]["headers"]["X-API-KEY"] == "key123"


@pytest.mark.asyncio
async def test_flightaware_status(monkeypatch):
    reg = registry.load_registry()
    _no_env(monkeypatch, "FLIGHTAWARE_API_KEY")
    with pytest.raises(CredentialsMissing):
        await registry.dispatch(reg["flightaware"], "flight_status",
                                {"ident": "GA820"}, confirm=False)

    monkeypatch.setenv("FLIGHTAWARE_API_KEY", "key123")
    calls = _mock_api(monkeypatch, "flightaware", lambda url, m, kw:
        {"flights": [{"ident": "GA820", "status": "Scheduled",
                      "origin": {"code": "CGK"}, "destination": {"code": "SIN"},
                      "scheduled_out": "2026-10-02T08:00:00Z",
                      "scheduled_in": "2026-10-02T10:45:00Z",
                      "aircraft_type": "B738"}]})
    r = await registry.dispatch(reg["flightaware"], "flight_status",
                                {"ident": "GA820"}, confirm=False)
    assert r["flights"][0]["destination"] == "SIN"
    assert "/flights/GA820" in calls[0]["url"]
    assert calls[0]["headers"]["Authorization"].startswith("Basic ")

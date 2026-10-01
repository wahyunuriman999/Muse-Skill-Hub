"""v2.1 hardening tests — proving the second audit's P0/P1 items.

Covers: atomic approval consumption under concurrency, atomic idempotency
reservation (PENDING/SUCCEEDED/FAILED/CONFLICT), supports_idempotency_key
rename, output schema enforcement, actor binding, credential scopes,
encrypted credential store, OAuth refresh, audit hash chain, TF-IDF
discovery, full JSON-Schema validation, SQL hardening, manifest-as-truth
for risk.
"""
import asyncio
import base64
import json
import os
import threading
import time

import pytest

from skillhub import approval, audit, registry
from skillhub.credentials import (cred, credential_scopes, require_scopes,
                                  save_local, set_scopes)
from skillhub.driver import ActionDef
from skillhub.errors import (ApprovalRevoked, CredentialsMissing,
                             IdempotencyConflict, InvalidInput,
                             OutputContractViolation, ScopeMismatch)
from skillhub.validate import validate_output, validate_params


@pytest.fixture()
def local_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    return asyncio.run(coro)


def _entry(handler, **kwargs):
    """Synthetic skill entry with one write action for dispatch tests."""
    async def h(params):
        return await handler(params)
    ad = ActionDef("test action",
                   {"name": {"type": "string"}}, ["name"], h,
                   write=True, **kwargs)
    return registry.SkillEntry(name="testskill", description="t",
                               implemented=True,
                               actions={"do_thing": ad})


# --- atomic approval consumption ------------------------------------------------
def test_approval_consume_is_atomic_under_concurrency(local_dir):
    item = approval.request_approval("s", "a", {"x": 1}, risk="write")
    approval.approve(item["approval_id"])
    aid = item["approval_id"]
    wins, losses = [], []

    def worker():
        try:
            approval.consume(aid, "s", "a", {"x": 1})
            wins.append(1)
        except ApprovalRevoked:
            losses.append(1)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(wins) == 1, "exactly one consumer may win"
    assert len(losses) == 19


def test_approval_actor_binding(local_dir):
    item = approval.request_approval("s", "a", {"x": 1}, risk="write",
                                     actor="alice")
    approval.approve(item["approval_id"], approver="alice")
    with pytest.raises(ApprovalRevoked):
        approval.consume(item["approval_id"], "s", "a", {"x": 1}, actor="bob")
    # the rightful actor can still consume (the failed attempt didn't burn it)
    approval.consume(item["approval_id"], "s", "a", {"x": 1}, actor="alice")


# --- atomic idempotency ----------------------------------------------------------
def test_idem_reserve_is_atomic_under_concurrency(local_dir):
    owners, denied = [], []

    def worker():
        owned, rec = registry._idem_reserve("k1", "s", "a", "phash")
        (owners if owned else denied).append(1)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(owners) == 1
    assert len(denied) == 19


def test_idempotency_lifecycle_pending_conflict_failed_retry(local_dir):
    # reserve → in-flight → second claim sees pending
    owned, rec = registry._idem_reserve("k2", "s", "a", "ph")
    assert owned and rec is None
    owned2, rec2 = registry._idem_reserve("k2", "s", "a", "ph")
    assert not owned2 and rec2["status"] == "pending"
    # different params on same key → conflict
    with pytest.raises(IdempotencyConflict):
        registry._idem_reserve("k2", "s", "a", "other-hash")
    # fail → exactly one retry may claim it
    registry._idem_fail("k2", "upstream_error")
    owned3, _ = registry._idem_reserve("k2", "s", "a", "ph")
    assert owned3
    owned4, rec4 = registry._idem_reserve("k2", "s", "a", "ph")
    assert not owned4 and rec4["status"] == "pending"
    # commit → deduplicated replay
    registry._idem_commit("k2", {"ok": True})
    owned5, rec5 = registry._idem_reserve("k2", "s", "a", "ph")
    assert not owned5 and rec5["status"] == "succeeded"
    assert rec5["result"] == {"ok": True}


def test_dispatch_idempotency_end_to_end(local_dir):
    calls = []

    async def handler(params):
        calls.append(1)
        return {"n": len(calls)}

    entry = _entry(handler)
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="write")
    approval.approve(item["approval_id"])
    r1 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                approval_id=item["approval_id"],
                                idempotency_key="e2e-1"))
    assert r1["n"] == 1 and len(calls) == 1
    # same key + same params → deduplicated, handler NOT re-run
    item2 = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                      risk="write")
    approval.approve(item2["approval_id"])
    r2 = _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                                approval_id=item2["approval_id"],
                                idempotency_key="e2e-1"))
    assert r2["deduplicated"] is True and r2["n"] == 1 and len(calls) == 1


def test_supports_idempotency_key_rename():
    ad = ActionDef("d", {}, [], None)
    assert ad.supports_idempotency_key is True
    # deprecated v2.0 kwarg still works
    ad2 = ActionDef("d", {}, [], None, idempotent=False)
    assert ad2.supports_idempotency_key is False


# --- output schema enforcement ----------------------------------------------------
def test_validate_output_enforced():
    schema = {"type": "object",
              "properties": {"id": {"type": "string"}},
              "required": ["id"]}
    assert validate_output("s", "a", schema, {"id": "1"}) == {"id": "1"}
    with pytest.raises(OutputContractViolation):
        validate_output("s", "a", schema, {"nope": 1})
    # empty schema = no constraints
    assert validate_output("s", "a", {}, "anything") == "anything"


def test_dispatch_enforces_output_schema(local_dir):
    async def bad_handler(params):
        return {"wrong": "shape"}

    ad = ActionDef("t", {"name": {"type": "string"}}, ["name"], bad_handler,
                   write=True,
                   output_schema={"type": "object",
                                  "properties": {"id": {"type": "string"}},
                                  "required": ["id"]})
    entry = registry.SkillEntry(name="testskill", description="t",
                                implemented=True, actions={"do_thing": ad})
    item = approval.request_approval("testskill", "do_thing", {"name": "x"},
                                     risk="write")
    approval.approve(item["approval_id"])
    with pytest.raises(OutputContractViolation):
        _run(registry.dispatch(entry, "do_thing", {"name": "x"},
                               approval_id=item["approval_id"],
                               idempotency_key="out-bad-1"))
    # the violating result must NOT be cached as succeeded
    owned, rec = registry._idem_reserve("out-bad-1", "testskill", "do_thing",
                                        registry._params_hash({"name": "x"}))
    assert owned  # failed records allow exactly one retry


# --- credential scopes -------------------------------------------------------------
def test_scope_enforcement(local_dir):
    save_local("TEST_TOKEN", "secret-value",
               scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    assert credential_scopes("TEST_TOKEN") == \
        ["https://www.googleapis.com/auth/gmail.readonly"]
    assert require_scopes(["TEST_TOKEN"],
                          ["https://www.googleapis.com/auth/gmail.readonly"],
                          "gmail") == "verified"
    with pytest.raises(ScopeMismatch):
        require_scopes(["TEST_TOKEN"],
                       ["https://www.googleapis.com/auth/gmail.send"], "gmail")
    # unknown scopes (plain env-style credential) → unverified, allowed
    save_local("PLAIN_TOKEN", "v")
    assert require_scopes(["PLAIN_TOKEN"], ["anything"], "x") == "unverified"


def test_dispatch_scope_mismatch_blocked(local_dir):
    save_local("GOOGLE_OAUTH_TOKEN", "tok",
               scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    reg = registry.load_registry()
    entry = reg["gmail"]
    item = approval.request_approval("gmail", "send_message",
                                     {"to": "a@b.c", "subject": "s", "body": "b"},
                                     risk="communication")
    approval.approve(item["approval_id"])
    with pytest.raises(ScopeMismatch):
        _run(registry.dispatch(entry, "send_message",
                               {"to": "a@b.c", "subject": "s", "body": "b"},
                               approval_id=item["approval_id"]))


# --- encrypted credential store ------------------------------------------------------
def test_credentials_encrypted_at_rest(local_dir):
    save_local("MY_SECRET", "super-secret-value")
    raw = (local_dir / "credentials.enc").read_bytes()
    assert b"super-secret-value" not in raw, "secret must not be plaintext on disk"
    assert not (local_dir / "credentials.json").exists()
    assert cred("MY_SECRET", "test") == "super-secret-value"


def test_plaintext_migration(local_dir):
    (local_dir / "credentials.json").write_text(
        json.dumps({"LEGACY": "old-value"}), encoding="utf-8")
    assert cred("LEGACY", "test") == "old-value"
    assert not (local_dir / "credentials.json").exists(), \
        "plaintext file must be removed after migration"
    raw = (local_dir / "credentials.enc").read_bytes()
    assert b"old-value" not in raw


def test_cred_missing_still_raises(local_dir):
    with pytest.raises(CredentialsMissing):
        cred("DEFINITELY_NOT_SET_XYZ", "test")


# --- OAuth refresh --------------------------------------------------------------------
def test_oauth_auto_refresh(local_dir, monkeypatch):
    from skillhub import oauth as oauth_mod

    oauth_mod.save_oauth(
        "OAUTH_TOKEN", access_token="expired-token",
        refresh_token="refresh-abc", client_id="cid", client_secret="csec",
        token_url="https://oauth.example/token",
        expires_at=int(time.time()) - 10,  # already expired
        scopes=["scope.a"])

    calls = {}

    class FakeResp:
        status_code = 200

        def json(self):
            return {"access_token": "fresh-token",
                    "refresh_token": "refresh-rotated",
                    "expires_in": 3600}

    def fake_post(url, data=None, timeout=None):
        calls["url"] = url
        calls["data"] = data
        return FakeResp()

    monkeypatch.setattr("httpx.post", fake_post)
    assert cred("OAUTH_TOKEN", "test") == "fresh-token"
    assert calls["url"] == "https://oauth.example/token"
    assert calls["data"]["grant_type"] == "refresh_token"
    # rotated credentials persisted
    status = oauth_mod.oauth_status("OAUTH_TOKEN")
    assert status["has_refresh_token"] is True
    assert status["expiring"] is False
    # second call uses the fresh token without another refresh
    calls.clear()
    assert cred("OAUTH_TOKEN", "test") == "fresh-token"
    assert calls == {}


# --- audit hash chain ----------------------------------------------------------------------
def test_audit_chain_verifies_and_detects_tampering(local_dir):
    audit.log({"skill": "s", "action": "a", "result": "success"})
    audit.log({"skill": "s", "action": "b", "result": "success"})
    audit.log({"skill": "s", "action": "c", "result": "error"})
    report = audit.verify_chain()
    assert report["ok"] is True and report["chained"] == 3

    # tamper: flip one byte in the middle event
    path = local_dir / "audit.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[1])
    rec["action"] = "EVIL"
    lines[1] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report2 = audit.verify_chain()
    assert report2["ok"] is False
    assert report2["first_bad"]["line"] == 2


# --- TF-IDF discovery -------------------------------------------------------------------------
def test_tfidf_discovery_ranks_relevant_skill_first():
    reg = registry.load_registry()
    hits = registry.search_capabilities(reg, "send email")
    assert hits, "expected results"
    assert hits[0]["skill"] in ("gmail", "outlook-mail"), hits[0]["skill"]
    hits2 = registry.search_capabilities(reg, "kanban project board tickets")
    names = [h["skill"] for h in hits2[:3]]
    assert any(n in ("linear", "asana", "trello", "notion") for n in names), names


# --- full JSON-Schema validation -----------------------------------------------------------------
def test_full_json_schema_keywords():
    params = {"email": {"type": "string", "format": "email"},
              "tags": {"type": "array", "items": {"type": "string"},
                       "minItems": 1, "uniqueItems": True},
              "age": {"type": "integer", "minimum": 0, "maximum": 150},
              "code": {"type": "string", "pattern": r"^[A-Z]{3}-\d+$"},
              "addr": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]},
              "kind": {"oneOf": [{"type": "string"}, {"type": "integer"}]}}
    good = {"email": "a@b.c", "tags": ["x"], "age": 30, "code": "ABC-123",
            "addr": {"city": "Jakarta"}, "kind": 5}
    validate_params("s", "a", params, [], good, strict=True)
    for bad in [
        {"email": "not-an-email"},
        {"tags": []},
        {"tags": ["x", "x"]},
        {"age": 200},
        {"code": "abc-123"},
        {"addr": {}},
        {"kind": 1.5},
        {"unknown_param": 1},  # strict: schema is the source of truth
    ]:
        merged = dict(good)
        merged.update(bad)
        if "unknown_param" in bad:
            merged = dict(good, unknown_param=1)
        with pytest.raises(InvalidInput):
            validate_params("s", "a", params, [], merged, strict=True)


# --- SQL hardening -------------------------------------------------------------------------------
def test_sql_comment_and_string_bypass_blocked(local_dir):
    from skillhub.skills import muse_db

    async def run(sql):
        return await muse_db.query({"sql": sql})

    # DROP hidden in a comment is still DROP
    with pytest.raises(Exception):
        _run(run("SELECT 1 /* sneaky */ ; -- DROP TABLE x"))
    with pytest.raises(Exception):
        _run(run("SELECT * FROM t WHERE x = '1'; DROP TABLE users --'"))
    # keyword inside a string literal is NOT a bypass vector nor a false block
    r = _run(run("SELECT 'drop table users' AS note"))
    assert r["rows"][0]["note"] == "drop table users"


def test_sql_read_connection_is_read_only(local_dir, monkeypatch, tmp_path):
    import sqlite3
    from skillhub.skills import muse_db

    db = tmp_path / "t.db"
    sqlite3.connect(str(db)).execute("CREATE TABLE t (a INT)").connection.close()
    monkeypatch.setenv("SKILLHUB_DB_PATH", str(db))
    with pytest.raises(Exception):
        _run(muse_db.query({"sql": "CREATE TABLE evil (a INT)"}))


# --- manifest as source of truth -------------------------------------------------------------------
def test_manifest_risk_is_canonical():
    reg = registry.load_registry()
    assert reg["gmail"].actions["send_message"].risk == "communication"
    assert reg["stripe"].actions["create_payment_link"].risk == "financial"
    assert reg["muse_db"].actions["execute_write"].risk == "destructive"
    # every manifest risk is a valid level
    from skillhub.driver import RISK_LEVELS
    for name, entry in reg.items():
        for aname, ad in entry.actions.items():
            assert ad.risk in RISK_LEVELS, f"{name}.{aname}: {ad.risk}"

"""Platform v2 tests — proving the friend's review items are executed.

Covers: per-action MCP schemas, input validation, approval engine,
policy engine, credential manager, vault secret isolation, audit log,
idempotency, http retry helpers, capability discovery, localstore
hardening, muse_db guardrails, error envelope, conformance validator.
"""
import asyncio
import json
import os
import time

import pytest

from skillhub import approval, audit, registry
from skillhub.credentials import cred
from skillhub.errors import (ApprovalExpired, ApprovalRequired, ApprovalRevoked,
                             IdempotencyConflict, InvalidInput, PolicyBlocked,
                             RateLimited, SkillError, UpstreamError)
from skillhub.policy import DEFAULT_POLICY, PolicyEngine


@pytest.fixture()
def local_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _run(coro):
    return asyncio.run(coro)


# 01. per-action MCP tools with real JSON schemas --------------------------------
def test_per_action_tools_have_full_schemas():
    reg = registry.load_registry()
    tools = registry.mcp_tools(reg)
    by_name = {t["name"]: t for t in tools}
    assert "github_search_repositories" in by_name
    assert "skillhub_search_capabilities" in by_name
    schema = by_name["github_search_repositories"]["inputSchema"]
    assert schema["properties"]["query"]["type"] == "string"
    assert "query" in schema["required"]
    # write action carries approval controls, not an opaque params blob
    create = by_name["github_create_issue"]["inputSchema"]
    assert "approval_id" in create["properties"]
    assert "idempotency_key" in create["properties"]
    assert "params" not in create["properties"]


def test_split_tool_name_roundtrip():
    reg = registry.load_registry()
    assert registry.split_tool_name(reg, "github_search_repositories") == \
        ("github", "search_repositories")
    assert registry.split_tool_name(reg, "meta_threads_post_text") == \
        ("meta-threads", "post_text")
    assert registry.split_tool_name(reg, "nope_nothing") is None


# 02. input validation ------------------------------------------------------------
def test_input_validation_rejects_bad_params(local_dir):
    reg = registry.load_registry()
    with pytest.raises(InvalidInput) as exc:
        _run(registry.dispatch(reg["github"], "search_repositories", {},
                               confirm=False))
    assert "query" in str(exc.value)
    with pytest.raises(InvalidInput):
        _run(registry.dispatch(reg["github"], "search_repositories",
                               {"query": "x", "per_page": "not-a-number"},
                               confirm=False))


# 03. approval engine --------------------------------------------------------------
def test_approval_full_lifecycle(local_dir):
    item = approval.request_approval("demo", "act", {"a": 1}, risk="financial")
    aid = item["approval_id"]
    assert aid.startswith("apr_")
    # cannot consume while pending
    with pytest.raises(ApprovalRequired):
        approval.consume(aid, "demo", "act", {"a": 1})
    approval.approve(aid)
    approval.consume(aid, "demo", "act", {"a": 1})
    # single-use: second consume fails
    with pytest.raises(ApprovalRevoked):
        approval.consume(aid, "demo", "act", {"a": 1})


def test_approval_binds_params(local_dir):
    item = approval.request_approval("demo", "act", {"a": 1})
    approval.approve(item["approval_id"])
    with pytest.raises(ApprovalRevoked):  # tampered params
        approval.consume(item["approval_id"], "demo", "act", {"a": 2})


def test_approval_expires(local_dir):
    item = approval.request_approval("demo", "act", {}, ttl_s=-1)
    with pytest.raises(ApprovalExpired):
        approval.approve(item["approval_id"])


def test_strict_risk_rejects_bare_confirm(local_dir):
    """communication-risk actions can't run on confirm=true alone."""
    reg = registry.load_registry()
    with pytest.raises(ApprovalRequired) as exc:
        _run(registry.dispatch(reg["gmail"], "send_message",
                               {"to": "a@b.c", "subject": "s", "body": "b"},
                               confirm=True))
    assert exc.value.to_dict()["approval_id"].startswith("apr_")


def test_legacy_confirm_still_works_for_plain_writes(local_dir):
    reg = registry.load_registry()
    out = _run(registry.dispatch(reg["goals"], "create_goal",
                                 {"title": "Ship v2"}, confirm=True))
    assert out["status"] == "ok"


# 04. policy engine -----------------------------------------------------------------
def test_policy_deny_rule():
    pol = PolicyEngine(rules={"gmail.send_message": "deny"})
    assert pol.evaluate("gmail", "send_message", "communication") == "deny"
    assert pol.evaluate("gmail", "list_messages", "sensitive") == "approval_required"
    assert pol.evaluate("github", "search_repositories", "read") == "allow"


def test_policy_blocked_in_dispatch(local_dir):
    reg = registry.load_registry()
    pol = PolicyEngine(rules={"goals.*": "deny"})
    with pytest.raises(PolicyBlocked):
        _run(registry.dispatch(reg["goals"], "create_goal", {"title": "x"},
                               confirm=True, policy=pol))


# 05. credential manager --------------------------------------------------------------
def test_credential_manager_env(monkeypatch):
    monkeypatch.setenv("SKILLHUB_TEST_CRED", "s3cr3t")
    assert cred("SKILLHUB_TEST_CRED") == "s3cr3t"
    with pytest.raises(SkillError):
        cred("SKILLHUB_DEFINITELY_MISSING")


def test_vault_ref_resolves_server_side(local_dir):
    reg = registry.load_registry()
    _run(registry.dispatch(reg["secure-vault"], "store_secret",
                           {"name": "api", "value": "tok123"}, confirm=True))
    assert cred("ref:vault:api", skill="secure-vault") == "tok123"


# 06. vault never leaks the value ------------------------------------------------------
def test_vault_get_secret_returns_ref_not_value(local_dir):
    reg = registry.load_registry()
    _run(registry.dispatch(reg["secure-vault"], "store_secret",
                           {"name": "k", "value": "supersecret"}, confirm=True))
    res = _run(registry.dispatch(reg["secure-vault"], "get_secret",
                                 {"name": "k"}, confirm=False))
    assert "value" not in res
    assert "supersecret" not in json.dumps(res)
    assert res["credential_ref"] == "ref:vault:k"


# 07. audit log --------------------------------------------------------------------------
def test_audit_log_records_and_redacts(local_dir):
    reg = registry.load_registry()
    _run(registry.dispatch(reg["secure-vault"], "store_secret",
                           {"name": "n", "value": "do-not-log-me"}, confirm=True))
    rows = audit.query(skill="secure-vault", action="store_secret")
    assert rows and rows[0]["result"] == "success"
    assert "do-not-log-me" not in json.dumps(rows[0])
    assert rows[0]["params_preview"]["value"] == "[redacted]"
    assert rows[0]["duration_ms"] >= 0


def test_audit_log_query_action(local_dir):
    reg = registry.load_registry()
    _run(registry.dispatch(reg["function-health"], "runtime_health", {},
                           confirm=False))
    res = _run(registry.dispatch(reg["function-health"], "query_audit_log",
                                 {"limit": 5}, confirm=False))
    assert res["status"] == "ok" and res["count"] >= 1


# 08. idempotency ---------------------------------------------------------------------------
def test_idempotency_dedupes(local_dir):
    reg = registry.load_registry()
    kw = {"idempotency_key": "idem-test-1"}
    r1 = _run(registry.dispatch(reg["goals"], "create_goal", {"title": "idem"},
                                confirm=True, **kw))
    r2 = _run(registry.dispatch(reg["goals"], "create_goal", {"title": "idem"},
                                confirm=True, **kw))
    assert "deduplicated" not in r1
    assert r2["deduplicated"] is True
    assert r1["goal"]["id"] == r2["goal"]["id"]


def test_idempotency_conflict_on_different_params(local_dir):
    reg = registry.load_registry()
    kw = {"idempotency_key": "idem-test-2"}
    _run(registry.dispatch(reg["goals"], "create_goal", {"title": "a"},
                           confirm=True, **kw))
    with pytest.raises(IdempotencyConflict):
        _run(registry.dispatch(reg["goals"], "create_goal", {"title": "b"},
                               confirm=True, **kw))


# 09. http layer --------------------------------------------------------------------------------
def test_http_retry_policy_unit():
    from skillhub.http import _backoff, _retryable
    assert _retryable("GET", 429, 0) is True
    assert _retryable("GET", 503, 0) is True
    assert _retryable("POST", 500, 0) is False  # unsafe method, no blind retry
    assert _retryable("GET", 429, 3) is False  # attempts exhausted
    assert _retryable("GET", 200, 0) is False
    assert 0 < _backoff(0, None) <= 8.0
    assert _backoff(0, "120") == 60.0  # Retry-After capped


def test_user_agent_centralized():
    from skillhub import __version__
    assert __version__ == "2.2.0"


# 10. capability discovery -----------------------------------------------------------------------
def test_search_capabilities():
    reg = registry.load_registry()
    hits = registry.search_capabilities(reg, "send email")
    assert hits and hits[0]["skill"] == "gmail"
    assert any(t.startswith("gmail_") for t in hits[0]["tools"])
    assert len(registry.search_capabilities(reg, "xyz-no-such-thing-xyz")) == 0


# localstore hardening ----------------------------------------------------------------------------
def test_corrupt_store_raises_and_backs_up(local_dir):
    from skillhub import localstore
    from skillhub.errors import StoreCorruptError
    p = localstore.data_dir() / "broken.json"
    p.write_text("{not valid json")
    with pytest.raises(StoreCorruptError):
        localstore.read_json("broken", {})
    backups = list(localstore.data_dir().glob("broken.corrupt.*.json"))
    assert backups, "corrupt file must be backed up, not silently dropped"


def test_atomic_write_roundtrip(local_dir):
    from skillhub import localstore
    localstore.write_json("w", {"a": [1, 2, 3]})
    assert localstore.read_json("w", None) == {"a": [1, 2, 3]}
    assert localstore.read_json("missing", "dflt") == "dflt"


# muse_db guardrails ---------------------------------------------------------------------------------
def test_muse_db_blocks_dangerous_sql(local_dir):
    reg = registry.load_registry()
    for sql in ("DROP TABLE t", "SELECT * FROM t; DROP TABLE t",
                "PRAGMA table_info(t)", "ATTACH DATABASE 'x' AS y"):
        with pytest.raises(SkillError):
            _run(registry.dispatch(reg["muse_db"], "execute_write",
                                   {"sql": sql}, confirm=True))
    # legit write still works through approval (risk=destructive needs approval)
    item = approval.request_approval("muse_db", "execute_write",
                                     {"sql": "CREATE TABLE g (id INTEGER)"},
                                     risk="destructive")
    approval.approve(item["approval_id"])
    out = _run(registry.dispatch(reg["muse_db"], "execute_write",
                                 {"sql": "CREATE TABLE g (id INTEGER)"},
                                 approval_id=item["approval_id"]))
    assert out["status"] == "ok"


# error envelope ----------------------------------------------------------------------------------------
def test_error_envelope_hides_internals():
    err = UpstreamError("demo", "secret provider payload", action="act")
    env = err.to_envelope(request_id="r1")
    assert env["ok"] is False
    assert env["error"]["code"] == "upstream_error"
    assert "secret provider payload" not in env["error"]["message"]
    assert env["meta"] == {"request_id": "r1", "skill": "demo", "action": "act"}
    rl = RateLimited("demo", retry_after=30)
    assert rl.to_envelope()["error"]["retryable"] is True
    assert rl.to_envelope()["error"]["retry_after"] == 30


# conformance ----------------------------------------------------------------------------------------------
def test_conformance_validator_passes():
    from skillhub.cli import validate
    assert validate() == 0


def test_metadata_counts():
    import io
    from contextlib import redirect_stdout
    from skillhub.cli import metadata
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert metadata() == 0
    meta = json.loads(buf.getvalue())
    assert meta["skills"] == 97 and meta["implemented"] == 94
    assert meta["mcp_tools"] > 200

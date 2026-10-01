"""GATE 1 — credential resolution / scope verification binding.

The guarantee: scope verification MUST run on the SAME resolved credential
object that value resolution produced — never on a same-named record from
a different source.

The v2.2.0 exploit this kills: ``cred("GITHUB_TOKEN")`` resolves the VALUE
from the environment, while ``require_scopes(["GITHUB_TOKEN"], ...)``
checked scopes from the ENCRYPTED STORE record of the same name. An env
token with unknown scopes was therefore reported "verified" because an
unrelated store record declared scopes. Scope confusion in both directions:

  * env value + store scopes  -> false "verified"   (privilege inflation)
  * env value + store DENY     -> false ScopeMismatch (denial of a valid credential)

Every test below encodes the CORRECT guarantee. They fail on v2.2.0
(no ``CredentialResolution`` exists) and pass after the fix.
"""
from __future__ import annotations

import os

import pytest

from skillhub import credentials as creds
from skillhub.errors import CredentialsMissing, ScopeMismatch


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Isolated data dir + clean env for credential names used here."""
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    for var in ("GATE1_TOKEN", "GATE1_OTHER"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


# --- resolution binds value + source + scopes in one object ---

def test_resolve_environment_binds_source(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_TOKEN", "env-value")
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert r.value == "env-value"
    assert r.source == "environment"
    assert r.name == "GATE1_TOKEN"


def test_resolve_encrypted_store_binds_source_and_scopes(isolated):
    creds.save_local("GATE1_TOKEN", "store-value", scopes=["repo", "user"])
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert r.value == "store-value"
    assert r.source == "encrypted_store"
    assert r.scopes == ["repo", "user"]


def test_resolve_vault_ref_binds_source(isolated):
    import asyncio
    from skillhub.skills import secure_vault
    asyncio.run(secure_vault.store_secret(
        {"name": "gate1secret", "value": "vault-value"}))
    r = creds.resolve_credential("ref:vault:gate1secret", skill="t")
    assert r.value == "vault-value"
    assert r.source == "vault"


def test_missing_credential_raises(isolated):
    with pytest.raises(CredentialsMissing):
        creds.resolve_credential("GATE1_TOKEN", skill="t")


# --- the scope-confusion exploit: MUST NOT verify across sources ---

def test_env_value_must_not_inherit_store_scopes(isolated, monkeypatch):
    """THE EXPLOIT. Env holds the token; the store holds a same-named
    record WITH scopes. v2.2.0 reported 'verified'. Correct: the resolved
    env credential has unknown scopes -> 'unverified'."""
    monkeypatch.setenv("GATE1_TOKEN", "env-value")
    creds.save_local("GATE1_TOKEN", "different-store-value",
                     scopes=["repo", "admin"])
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert r.value == "env-value"          # env wins for the value
    assert r.source == "environment"
    assert r.scopes is None                # ...and does NOT inherit store scopes
    assert creds.require_scopes(r, ["repo"], skill="t") == "unverified"


def test_store_deny_must_not_block_env_credential(isolated, monkeypatch):
    """Reverse confusion: store record lacks scopes, but the credential in
    use is the env one (scopes unknown, allowed with audit note)."""
    monkeypatch.setenv("GATE1_TOKEN", "env-value")
    creds.save_local("GATE1_TOKEN", "different-store-value", scopes=["other"])
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    # must NOT raise ScopeMismatch for the store record's scopes
    assert creds.require_scopes(r, ["repo"], skill="t") == "unverified"


def test_vault_ref_must_not_inherit_store_scopes(isolated):
    import asyncio
    from skillhub.skills import secure_vault
    asyncio.run(secure_vault.store_secret(
        {"name": "gate1secret", "value": "vault-value"}))
    creds.save_local("gate1secret", "store-value", scopes=["repo"])
    r = creds.resolve_credential("ref:vault:gate1secret", skill="t")
    assert r.source == "vault"
    assert r.scopes is None
    assert creds.require_scopes(r, ["repo"], skill="t") == "unverified"


# --- same-object scope verification ---

def test_store_scopes_sufficient_verifies(isolated):
    creds.save_local("GATE1_TOKEN", "v", scopes=["repo", "user"])
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert creds.require_scopes(r, ["repo"], skill="t") == "verified"
    assert r.scope_status == "verified"


def test_store_scopes_insufficient_raises(isolated):
    creds.save_local("GATE1_TOKEN", "v", scopes=["user"])
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    with pytest.raises(ScopeMismatch):
        creds.require_scopes(r, ["repo", "admin"], skill="t")


def test_store_without_scopes_is_unverified(isolated):
    creds.save_local("GATE1_TOKEN", "v")
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert creds.require_scopes(r, ["repo"], skill="t") == "unverified"


def test_no_required_scopes_is_verified(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_TOKEN", "v")
    r = creds.resolve_credential("GATE1_TOKEN", skill="t")
    assert creds.require_scopes(r, [], skill="t") == "verified"


# --- resolve_any binds the winning source ---

def test_resolve_any_first_available(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_OTHER", "other-env")
    r = creds.resolve_any("GATE1_TOKEN", "GATE1_OTHER", skill="t")
    assert r.name == "GATE1_OTHER"
    assert r.source == "environment"


def test_resolve_any_prefers_environment_over_store(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_TOKEN", "env-value")
    creds.save_local("GATE1_TOKEN", "store-value", scopes=["repo"])
    r = creds.resolve_any("GATE1_TOKEN", skill="t")
    assert r.source == "environment"
    assert r.scopes is None


def test_resolve_any_none_missing_raises(isolated):
    with pytest.raises(CredentialsMissing):
        creds.resolve_any("GATE1_TOKEN", "GATE1_OTHER", skill="t")


# --- backward compatibility: value-only wrappers still work ---

def test_cred_still_returns_value(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_TOKEN", "env-value")
    assert creds.cred("GATE1_TOKEN", skill="t") == "env-value"
    creds.save_local("GATE1_OTHER", "store-value")
    assert creds.cred("GATE1_OTHER", skill="t") == "store-value"


def test_cred_any_still_returns_value(isolated, monkeypatch):
    monkeypatch.setenv("GATE1_OTHER", "other-env")
    assert creds.cred_any("GATE1_TOKEN", "GATE1_OTHER", skill="t") == "other-env"


# --- dispatch integration: audit carries source + scope evidence ---

def test_dispatch_audits_credential_source_and_scope_check(isolated,
                                                           monkeypatch):
    """Hermetic: a fake local skill entry with required_env + required_scopes.
    The audit trail must carry credential_source (name:source pairs) and
    scope_check, and never the secret value."""
    import asyncio
    import json
    from skillhub import localstore, registry
    from skillhub.driver import ActionDef
    monkeypatch.setenv("GATE1_TOKEN", "env-value")

    async def _handler(params):
        return {"ok": True}

    action_def = ActionDef(
        description="gate1 probe", handler=_handler, risk="read",
        required_scopes=["some:scope"],
        output_schema={"type": "object"},
    )
    entry = registry.SkillEntry(
        name="gate1-skill", description="gate1 probe", implemented=True,
        actions={"probe": action_def}, required_env=["GATE1_TOKEN"],
    )
    asyncio.run(registry.dispatch(entry, "probe", {}, actor="gate1"))
    trail = (localstore.data_dir() / "audit.jsonl").read_text(
        encoding="utf-8")
    assert "env-value" not in trail  # the secret value never lands in audit
    rec = json.loads(trail.strip().splitlines()[-1])
    assert rec["credential_source"] == "GATE1_TOKEN:environment"
    # env credential declares no scopes -> unverified (NOT false "verified")
    assert rec["scope_check"] == "unverified"

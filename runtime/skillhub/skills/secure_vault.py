"""Secure vault — LOCAL encrypted reference implementation.

Real AES encryption (Fernet) with a local encrypted file store. This is a
reference implementation of the vault interface — it is NOT connected to any
cloud vault. Swap the storage backend for production use.

Setup: set SKILLHUB_VAULT_KEY to a Fernet key (or leave unset to auto-generate
one, stored with 0600 permissions). pip install cryptography (already in test env).
"""
from __future__ import annotations

import base64
import json
import os
import time
from contextlib import contextmanager

from ..driver import ActionDef
from ..errors import SkillError, StoreCorruptError
from ..localstore import LOCAL_NOTE, data_dir

SKILL = "secure-vault"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("Set SKILLHUB_VAULT_KEY to a Fernet key "
              "(generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'). "
              "If unset, one is generated and stored locally. " + LOCAL_NOTE)

_VAULT_FILE = "vault.enc.json"
_VAULT_LOCK = "vault.lock"  # separate lock file; never the data file itself


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise SkillError(SKILL, "missing_dependency",
                         "pip install cryptography to enable the vault.") from exc
    key_path = data_dir() / "vault.key"
    key = os.environ.get("SKILLHUB_VAULT_KEY")
    if not key:
        if key_path.exists():
            key = key_path.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            key_path.write_text(key)
            os.chmod(key_path, 0o600)
    return Fernet(key.encode())


def _load() -> dict:
    """Read the vault. Missing file → {}. Corrupt file → backed up and
    StoreCorruptError (fail-closed: NEVER silently return {} or partial
    data — a corrupt vault must be explicit, not invisible)."""
    p = data_dir() / _VAULT_FILE
    if not p.exists():
        return {}
    try:
        f = _fernet()
        return json.loads(f.decrypt(p.read_bytes()).decode())
    except Exception as exc:
        backup = data_dir() / f"vault.corrupt.{int(time.time())}.enc.json"
        try:
            os.replace(p, backup)
        except OSError:
            backup = p
        raise StoreCorruptError(SKILL, str(backup)) from exc


def _save_nolock(vault: dict) -> None:
    """Crash-atomic write: tmp + fsync + os.replace. Caller MUST hold the
    vault lock (see _locked_vault) — the data file itself is never locked."""
    f = _fernet()
    payload = f.encrypt(json.dumps(vault).encode())
    p = data_dir() / _VAULT_FILE
    tmp = data_dir() / f"vault.enc.json.tmp.{os.getpid()}"
    with open(tmp, "wb") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, p)


def _save(vault: dict) -> None:
    """Replace the whole vault, crash-atomically, under the vault lock."""
    with _locked_vault() as current:
        current.clear()
        current.update(vault)


@contextmanager
def _locked_vault():
    """Serialized read-modify-write on the vault.

    The exclusive cross-process lock lives on the separate ``vault.lock``
    file; the data file is written crash-atomically (tmp + fsync +
    replace), so this is atomic against both concurrency AND crashes.
    Yields the mutable vault dict and saves it on clean exit.
    """
    from .. import filelock

    with filelock.locked(data_dir() / _VAULT_LOCK):
        vault = _load()
        yield vault
        _save_nolock(vault)


def _read_secret_value(name: str) -> str | None:
    """Server-side only. Never expose through an MCP tool response."""
    return _load().get(name)


async def store_secret(params: dict) -> dict:
    with _locked_vault() as vault:
        vault[params["name"]] = params["value"]
    return {"status": "ok", "stored": params["name"]}


async def get_secret(params: dict) -> dict:
    """Return a credential_ref, NOT the value.

    The value never leaves the runtime. Drivers resolve ``ref:vault:<name>``
    server-side via skillhub.credentials. Use ``reveal_secret`` (write +
    confirm, audit-logged) only when the user explicitly asks to see it.
    """
    if params["name"] not in _load():
        raise SkillError(SKILL, "not_found", f"No secret named '{params['name']}'.")
    return {"status": "ok", "name": params["name"],
            "credential_ref": f"ref:vault:{params['name']}",
            "usage": "Pass credential_ref as a parameter to drivers that accept "
                     "vault references; the runtime resolves it server-side."}


async def reveal_secret(params: dict) -> dict:
    """Explicitly reveal a secret value (write + confirm, audit-logged).

    Only for cases where the user themselves asked to see the value.
    Prefer credential_ref for agent-to-driver flows.
    """
    vault = _load()
    if params["name"] not in vault:
        raise SkillError(SKILL, "not_found", f"No secret named '{params['name']}'.")
    return {"status": "ok", "name": params["name"],
            "value": vault[params["name"]],
            "warning": "This reveal was audit-logged. Do not paste secrets into prompts."}


async def delete_secret(params: dict) -> dict:
    with _locked_vault() as vault:
        vault.pop(params["name"], None)
    return {"status": "ok", "deleted": params["name"]}


async def list_secrets(params: dict) -> dict:
    return {"status": "ok", "secrets": sorted(_load().keys())}


ACTIONS = {
    "store_secret": ActionDef("Store a secret in the encrypted local vault (needs confirm=true).",
        {"name": {"type": "string"}, "value": {"type": "string"}},
        ["name", "value"], store_secret, write=True, sensitive_params=["value"]),
    "get_secret": ActionDef("Get a credential_ref for a secret (the VALUE is never returned to the LLM).",
        {"name": {"type": "string"}}, ["name"], get_secret),
    "reveal_secret": ActionDef("Reveal a secret value explicitly (needs confirm=true; audit-logged; prefer credential_ref).",
        {"name": {"type": "string"}}, ["name"], reveal_secret, write=True, risk="sensitive"),
    "delete_secret": ActionDef("Delete a secret (needs approval: irreversible).",
        {"name": {"type": "string"}}, ["name"], delete_secret, risk="destructive"),
    "list_secrets": ActionDef("List secret names (never values).", {}, [], list_secrets),
}

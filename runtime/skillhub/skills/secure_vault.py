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

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, data_dir

SKILL = "secure-vault"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("Set SKILLHUB_VAULT_KEY to a Fernet key "
              "(generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'). "
              "If unset, one is generated and stored locally. " + LOCAL_NOTE)


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
    p = data_dir() / "vault.enc.json"
    if not p.exists():
        return {}
    f = _fernet()
    return json.loads(f.decrypt(p.read_bytes()).decode())


def _save(vault: dict) -> None:
    f = _fernet()
    (data_dir() / "vault.enc.json").write_bytes(f.encrypt(
        json.dumps(vault).encode()))


def _read_secret_value(name: str) -> str | None:
    """Server-side only. Never expose through an MCP tool response."""
    return _load().get(name)


async def store_secret(params: dict) -> dict:
    vault = _load()
    vault[params["name"]] = params["value"]
    _save(vault)
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
    vault = _load()
    vault.pop(params["name"], None)
    _save(vault)
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
    "delete_secret": ActionDef("Delete a secret (needs confirm=true).",
        {"name": {"type": "string"}}, ["name"], delete_secret, write=True),
    "list_secrets": ActionDef("List secret names (never values).", {}, [], list_secrets),
}

"""Credential manager — one subsystem for all secret resolution.

Resolution order for a credential ``name``:
1. Environment variable (``name`` as-is, e.g. ``GITHUB_TOKEN``)
2. ``vault:<secret-name>`` references → resolved server-side from the
   encrypted secure vault (the LLM never sees the value)
3. ``~/.skillhub-local/credentials.json`` (JSON map, file mode 0600)

Drivers should call::

    from skillhub.credentials import cred
    token = cred("GITHUB_TOKEN")                       # env or local file
    token = cred("ref:vault:gmail-prod")               # vault-backed, server-side

A ``ref:vault:<name>`` can be passed by the LLM as an ordinary string
parameter — the value is resolved inside the runtime and never rendered
into prompts, logs, or tool outputs.
"""
from __future__ import annotations

import json
import os
import stat

from . import localstore
from .errors import CredentialsMissing

VAULT_REF_PREFIX = "ref:vault:"


def _local_file() -> dict:
    path = localstore.data_dir() / "credentials.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_local(name: str, value: str) -> None:
    """Store a credential in the local file (mode 0600). Prefer the vault."""
    path = localstore.data_dir() / "credentials.json"
    data = _local_file()
    data[name] = value
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def resolve_vault_ref(name: str, skill: str = "credentials") -> str:
    """Resolve ``vault:<name>`` server-side. Raises if missing."""
    from .skills import secure_vault  # local import: driver module

    value = secure_vault._read_secret_value(name)
    if value is None:
        raise CredentialsMissing(skill, [f"vault:{name}"],
                                 "Store it first with secure-vault store_secret.")
    return value


def cred(name: str, skill: str = "unknown") -> str:
    """Resolve a credential by name or vault reference."""
    if name.startswith(VAULT_REF_PREFIX):
        return resolve_vault_ref(name[len(VAULT_REF_PREFIX):], skill=skill)
    value = os.environ.get(name) or _local_file().get(name)
    if not value:
        raise CredentialsMissing(
            skill, [name],
            "Set it as an environment variable, save it with "
            "credentials.save_local, or use a ref:vault:<name> reference.")
    return value


def maybe_resolve(value: str | None, skill: str = "unknown") -> str | None:
    """Resolve only if the value is a vault reference; else pass through."""
    if value and value.startswith(VAULT_REF_PREFIX):
        return cred(value, skill=skill)
    return value

"""Credential manager — one subsystem for all secret resolution.

Resolution order for a credential ``name``:
1. Environment variable (``name`` as-is, e.g. ``GITHUB_TOKEN``)
2. ``ref:vault:<name>`` references → resolved server-side from the
   encrypted secure vault (the LLM never sees the value)
3. Encrypted local store ``~/.skillhub-local/credentials.enc``
   (Fernet, same key machinery as the secure vault — see below)

Drivers should call::

    from ..credentials import cred, cred_any, maybe_cred
    token = cred("GITHUB_TOKEN", SKILL)            # env / vault / encrypted file
    token = cred_any("A_TOKEN", "B_TOKEN", skill=SKILL)  # first that resolves
    token = maybe_cred("OPTIONAL_TOKEN", SKILL)   # None instead of raising

A ``ref:vault:<name>`` can be passed by the LLM as an ordinary string
parameter — the value is resolved inside the runtime and never rendered
into prompts, logs, or tool outputs.

Security model (honest): the encrypted local store protects against
casual disk theft / backup leaks. It does NOT protect against a
compromised user account or malware running as the user — the key lives
on the same machine. For hostile environments use env vars injected by a
real secret manager, or the encrypted vault with an external
SKILLHUB_VAULT_KEY.

Scopes: a stored credential may declare OAuth scopes
(``save_local(name, value, scopes=[...])`` or ``set_scopes``). Actions
declare ``required_scopes``; ``require_scopes`` enforces them when the
credential's scopes are known. Credentials whose scopes are unknown
(plain env vars) are allowed with an audit note — this runtime is a
single-user local boundary, not a multi-tenant OAuth gateway.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager

from . import localstore
from .errors import (CredentialStoreCorruptError, CredentialsMissing,
                     ScopeMismatch)

VAULT_REF_PREFIX = "ref:vault:"
_ENC_STORE = "credentials.enc"
_LOCK_NAME = "credentials"  # localstore lock: <datadir>/credentials.lock


def _fernet():
    from .skills import secure_vault  # local import: driver module
    return secure_vault._fernet()


def _enc_path():
    return localstore.data_dir() / _ENC_STORE


def _lock():
    """The credentials lock (separate lock file; never the store itself)."""
    from . import filelock
    return filelock.locked(localstore.data_dir() / f"{_LOCK_NAME}.lock")


def _read_store_nolock() -> dict:
    """Raw read + plaintext migration. Caller MUST hold the credentials lock."""
    _migrate_plaintext_nolock()
    path = _enc_path()
    if not path.exists():
        return {}
    try:
        raw = _fernet().decrypt(path.read_bytes())
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        backup = path.with_name(
            f"credentials.corrupt.{int(time.time())}.enc")
        try:
            os.replace(path, backup)
        except OSError:
            backup = path
        raise CredentialStoreCorruptError(str(backup)) from exc


def _read_store() -> dict:
    """Read the encrypted credential store (migrating plaintext if needed).

    Missing file → {}. Present but undecryptable/corrupt →
    CredentialStoreCorruptError (fail-closed: never silently "empty").
    """
    with _lock():
        return _read_store_nolock()


def _write_store(data: dict) -> None:
    """Crash-atomic write: tmp + fsync + os.replace. Caller holds the lock."""
    path = _enc_path()
    payload = _fernet().encrypt(
        json.dumps(data, ensure_ascii=False).encode("utf-8"))
    tmp = path.with_name(f"credentials.enc.tmp.{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


@contextmanager
def _locked_store():
    """Exclusive cross-process read-modify-write on the credential store.

    The lock lives on a separate ``credentials.lock`` file; the store
    itself is written crash-atomically (tmp + fsync + replace), so this
    is atomic against both concurrency AND crashes.
    """
    with _lock():
        data = _read_store_nolock()
        yield data
        _write_store(data)


def _migrate_plaintext_nolock() -> None:
    """One-way migration: plaintext credentials.json → encrypted store.

    Caller MUST hold the credentials lock.
    """
    legacy = localstore.data_dir() / "credentials.json"
    if not legacy.exists():
        return
    try:
        old = json.loads(legacy.read_text(encoding="utf-8"))
    except Exception:
        old = {}
    if isinstance(old, dict) and old:
        path = _enc_path()
        data: dict = {}
        if path.exists():
            try:
                raw = _fernet().decrypt(path.read_bytes())
                parsed = json.loads(raw.decode("utf-8"))
                data = parsed if isinstance(parsed, dict) else {}
            except Exception:
                # corrupt existing store → leave it for _read_store_nolock's
                # fail-closed handling on next read; still delete legacy
                # plaintext so no secret lingers on disk
                pass
        for name, value in old.items():
            if isinstance(value, str) and name not in data:
                data[name] = {"value": value, "scopes": None,
                              "updated_at": int(time.time())}
        _write_store(data)
    try:
        legacy.unlink()
    except OSError:
        pass


def save_local(name: str, value: str, scopes: list[str] | None = None) -> None:
    """Store a credential in the encrypted local store. Prefer the vault."""
    with _locked_store() as data:
        data[name] = {"value": value, "scopes": list(scopes) if scopes else None,
                      "updated_at": int(time.time())}


def set_scopes(name: str, scopes: list[str]) -> None:
    """Attach OAuth scopes to a stored credential name."""
    with _locked_store() as data:
        rec = data.get(name) or {}
        if isinstance(rec, str):  # tolerate legacy plain-string records
            rec = {"value": rec}
        rec["scopes"] = list(scopes)
        rec["updated_at"] = int(time.time())
        data[name] = rec


def credential_scopes(name: str) -> list[str] | None:
    """Scopes declared for a credential, or None if unknown."""
    rec = _read_store().get(name)
    if isinstance(rec, dict):
        return rec.get("scopes")
    return None


def _stored_value(name: str) -> tuple[str | None, dict]:
    rec = _read_store().get(name)
    if isinstance(rec, dict):
        return rec.get("value"), rec
    return None, {}


def has(name: str) -> bool:
    """True if the credential resolves from any source (env/vault/encrypted)."""
    if name.startswith(VAULT_REF_PREFIX):
        from .skills import secure_vault  # local import: driver module
        return secure_vault._read_secret_value(
            name[len(VAULT_REF_PREFIX):]) is not None
    if os.environ.get(name):
        return True
    value, _ = _stored_value(name)
    return bool(value)


def resolve_vault_ref(name: str, skill: str = "credentials") -> str:
    """Resolve ``vault:<name>`` server-side. Raises if missing."""
    from .skills import secure_vault  # local import: driver module

    value = secure_vault._read_secret_value(name)
    if value is None:
        raise CredentialsMissing(skill, [f"vault:{name}"],
                                 "Store it first with secure-vault store_secret.")
    return value


def _maybe_refresh(name: str, rec: dict, skill: str) -> str | None:
    """Auto-refresh an OAuth access token when refresh metadata is stored."""
    oauth = rec.get("oauth")
    if not oauth or not rec.get("value"):
        return rec.get("value")
    from . import oauth as oauth_mgr
    return oauth_mgr.get_valid_token(name, rec, skill)


def cred(name: str, skill: str = "unknown") -> str:
    """Resolve a credential by name or vault reference. Raises if missing."""
    if name.startswith(VAULT_REF_PREFIX):
        return resolve_vault_ref(name[len(VAULT_REF_PREFIX):], skill=skill)
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    value, rec = _stored_value(name)
    if value:
        refreshed = _maybe_refresh(name, rec, skill)
        if refreshed:
            return refreshed
        return value
    raise CredentialsMissing(
        skill, [name],
        "Set it as an environment variable, store it encrypted with "
        "credentials.save_local, or use a ref:vault:<name> reference.")


def cred_any(*names: str, skill: str = "unknown") -> str:
    """Resolve the first credential name that has a value. Raises if none."""
    for name in names:
        try:
            return cred(name, skill=skill)
        except CredentialsMissing:
            continue
    raise CredentialsMissing(skill, list(names),
                             "Set one of these as an environment variable, "
                             "store it encrypted, or use a ref:vault:<name>.")


def maybe_cred(name: str, skill: str = "unknown") -> str | None:
    """Like cred() but returns None instead of raising when missing."""
    try:
        return cred(name, skill=skill)
    except CredentialsMissing:
        return None


def maybe_resolve(value: str | None, skill: str = "unknown") -> str | None:
    """Resolve only if the value is a vault reference; else pass through."""
    if value and value.startswith(VAULT_REF_PREFIX):
        return cred(value, skill=skill)
    return value


def require_scopes(credential_names: list[str], required: list[str],
                   skill: str = "unknown") -> str:
    """Enforce credential scopes for an action.

    Returns ``"verified"`` when a stored credential's declared scopes cover
    ``required``, ``"unverified"`` when no credential declares scopes (plain
    env vars — allowed with an audit note on this single-user runtime).
    Raises ScopeMismatch when declared scopes are insufficient.
    """
    if not required:
        return "verified"
    for name in credential_names:
        scopes = credential_scopes(name)
        if scopes is None:
            continue
        missing = [s for s in required if s not in scopes]
        if missing:
            raise ScopeMismatch(
                f"Credential '{name}' lacks required scopes: {missing}. "
                f"Action requires {required}; credential declares {scopes}.",
                skill=skill)
        return "verified"
    return "unverified"

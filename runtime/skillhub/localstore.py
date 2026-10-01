"""Local JSON store helper for reference-implementation drivers (v2, hardened).

Drivers for Muse platform capabilities (vault, feed, ideas, permissions, ...)
have no public cloud API. They run as honest LOCAL reference implementations:
real logic, real local storage under ~/.skillhub-local/ (override with
SKILLHUB_LOCAL_DIR). Every such driver documents this in its SETUP_HELP —
swap the storage backend for production use.

Hardening guarantees:
- atomic writes (tmp file + os.replace) — no half-written JSON
- advisory file locking (fcntl) around read-modify-write cycles
- restrictive permissions (0600) on the data directory
- corrupt files are NEVER silently replaced with defaults: the corrupt file
  is backed up to ``<name>.corrupt.<timestamp>.json`` and StoreCorruptError
  is raised so the failure is explicit.
"""
from __future__ import annotations

import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path


def data_dir() -> Path:
    d = Path(os.environ.get("SKILLHUB_LOCAL_DIR", Path.home() / ".skillhub-local"))
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


@contextmanager
def _locked(path: Path, mode: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode) as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield fh
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _path(name: str) -> Path:
    return data_dir() / f"{name}.json"


def read_json(name: str, default):
    """Read a JSON store. Missing file → default. Corrupt file → backup + raise."""
    from .errors import StoreCorruptError

    p = _path(name)
    if not p.exists():
        return default
    try:
        with _locked(p, "r") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        backup = p.with_name(f"{name}.corrupt.{int(time.time())}.json")
        try:
            p.replace(backup)
        except OSError:
            backup = p
        raise StoreCorruptError(name, str(backup)) from exc


def write_json(name: str, data) -> None:
    """Atomic write: tmp file + os.replace, under an exclusive lock."""
    p = _path(name)
    tmp = p.with_name(f"{name}.tmp.{os.getpid()}")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    with _locked(tmp, "w") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)


def append_jsonl(name: str, record: dict) -> None:
    """Append one JSON line atomically (used by the audit log)."""
    p = data_dir() / f"{name}.jsonl"
    line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
    with _locked(p, "a") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


LOCAL_NOTE = (
    "Local reference implementation: real logic with local file storage "
    "(~/.skillhub-local/, override with SKILLHUB_LOCAL_DIR). "
    "It does not connect to any cloud backend — swap the storage layer for production."
)

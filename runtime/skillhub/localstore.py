"""Local JSON store helper for reference-implementation drivers (v2, hardened).

Drivers for Muse platform capabilities (vault, feed, ideas, permissions, ...)
have no public cloud API. They run as honest LOCAL reference implementations:
real logic, real local storage under ~/.skillhub-local/ (override with
SKILLHUB_LOCAL_DIR). Every such driver documents this in its SETUP_HELP —
swap the storage backend for production use.

Hardening guarantees:
- crash-atomic writes (tmp file + fsync + os.replace) — no half-written JSON,
  even if the process dies mid-write
- cross-process locking via :mod:`skillhub.filelock` (fcntl on Unix,
  msvcrt on Windows) — no top-level ``import fcntl`` anywhere
- the lock lives on a *separate* ``<name>.lock`` file: the data file may be
  atomically replaced while the lock's inode stays stable
- restrictive permissions (0600) on the data directory
- corrupt files are NEVER silently replaced with defaults: the corrupt file
  is backed up to ``<name>.corrupt.<timestamp>.json`` and StoreCorruptError
  is raised so the failure is explicit.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from . import filelock


def data_dir() -> Path:
    d = Path(os.environ.get("SKILLHUB_LOCAL_DIR", Path.home() / ".skillhub-local"))
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _path(name: str) -> Path:
    return data_dir() / f"{name}.json"


def _lock_path(name: str) -> Path:
    return data_dir() / f"{name}.lock"


def _read_parsed(path: Path, name: str, default):
    """Parse without locking (caller must hold the lock)."""
    from .errors import StoreCorruptError

    if not path.exists():
        return default() if callable(default) else default
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StoreCorruptError(name, str(path)) from exc
    if not raw.strip():
        return default() if callable(default) else default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        backup = path.with_name(f"{name}.corrupt.{int(time.time())}.json")
        try:
            os.replace(path, backup)
        except OSError:
            backup = path
        raise StoreCorruptError(name, str(backup)) from exc


def _write_atomic(path: Path, data) -> None:
    """Crash-atomic write: tmp + fsync + os.replace (caller holds the lock)."""
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


@contextmanager
def locked(path: Path, mode: str = "a+b"):
    """Yield a handle to ``path`` (opened with ``mode``) under an exclusive,
    cross-process lock.

    The lock itself lives on a separate ``<path>.lock`` file, so ``path``
    may be atomically replaced while the lock is held. Kept compatible
    with the old ``fcntl``-based helper: callers still get a real file
    handle they can seek/read/write.
    """
    path = Path(path)
    with filelock.locked(Path(str(path) + ".lock")):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode) as fh:
            yield fh


@contextmanager
def shared_locked(path: Path, mode: str = "r"):
    """Yield a handle to ``path`` under a shared (read) cross-process lock."""
    path = Path(path)
    with filelock.shared_locked(Path(str(path) + ".lock")):
        with open(path, mode) as fh:
            yield fh


def read_json(name: str, default):
    """Read a JSON store. Missing file → default. Corrupt file → backup + raise."""
    with filelock.locked(_lock_path(name)):
        return _read_parsed(_path(name), name, default)


def write_json(name: str, data) -> None:
    """Crash-atomic write (tmp + fsync + os.replace) under the store lock."""
    with filelock.locked(_lock_path(name)):
        _write_atomic(_path(name), data)


def append_jsonl(name: str, record: dict) -> None:
    """Append one JSON line atomically (used by the audit log)."""
    p = data_dir() / f"{name}.jsonl"
    line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
    with filelock.locked(data_dir() / f"{name}.lock"):
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


@contextmanager
def locked_json(name: str, default):
    """Atomic read-modify-write critical section.

    The whole cycle — read, yield the mutable data, write back — happens
    under one cross-process exclusive lock taken on a *separate*
    ``<name>.lock`` file, and the write-back is crash-atomic
    (tmp + fsync + ``os.replace``). So this is atomic in BOTH senses:

    - concurrency-atomic: the check and the state change happen inside ONE
      locked section, never as separate read/write calls — two processes
      cannot both observe ``approved`` and both consume it;
    - crash-atomic: a crash mid-write leaves either the old file or the
      new file, never a truncated one.

    Corrupt files are backed up and raise StoreCorruptError (never silently
    replaced), same as :func:`read_json`.
    """
    with filelock.locked(_lock_path(name)):
        data = _read_parsed(_path(name), name, default)
        yield data
        _write_atomic(_path(name), data)


LOCAL_NOTE = (
    "Local reference implementation: real logic with local file storage "
    "(~/.skillhub-local/, override with SKILLHUB_LOCAL_DIR). "
    "It does not connect to any cloud backend — swap the storage layer for production."
)

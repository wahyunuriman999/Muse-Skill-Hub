"""Cross-platform advisory file locking.

``fcntl`` (Unix) does not exist on Windows, and a top-level
``import fcntl`` breaks the whole runtime there — ``server → registry →
localstore → import fcntl`` fails at import time. This module hides the
platform behind one small API so every store uses it instead of touching
``fcntl``/``msvcrt`` directly.

- Unix (Linux, macOS): ``fcntl.flock``
- Windows: ``msvcrt.locking`` (mandatory-style byte-range lock on 1 byte)

Both are advisory/cross-process: two processes (or threads) racing on the
same lock file get exactly one holder. Locks are always taken on a
*separate* ``<name>.lock`` file, never on the data file itself — the data
file may be atomically replaced (tmp + ``os.replace``) while the lock's
inode stays stable.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import msvcrt
else:
    import fcntl


@contextmanager
def locked(lock_path: str | Path):
    """Hold an exclusive cross-process lock on ``lock_path``.

    The lock file is created if missing. The same file must be used by
    every participant guarding a given resource.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # "a+b" creates the file if missing without truncating it
    with open(lock_path, "a+b") as fh:
        _acquire(fh, exclusive=True)
        try:
            yield fh
        finally:
            _release(fh, exclusive=True)


@contextmanager
def shared_locked(lock_path: str | Path):
    """Hold a shared (read) cross-process lock on ``lock_path``."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+b") as fh:
        _acquire(fh, exclusive=False)
        try:
            yield fh
        finally:
            _release(fh, exclusive=False)


def _acquire(fh, exclusive: bool) -> None:
    if _IS_WINDOWS:
        # LK_LOCK blocks until the 1-byte region is free; LK_UNLCK releases.
        # Lock the first byte; the file is at least 1 byte after "a+b" open
        # on an empty file? msvcrt needs the region to exist — ensure size.
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write(b"\x00")
            fh.flush()
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)


def _release(fh, exclusive: bool) -> None:
    if _IS_WINDOWS:
        fh.seek(0)
        try:
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def platform_name() -> str:
    """'windows' or 'unix' — exposed for tests and diagnostics."""
    return "windows" if _IS_WINDOWS else "unix"

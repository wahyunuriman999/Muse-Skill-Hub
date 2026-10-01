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

Threading: a per-path ``threading.RLock`` is held for the duration of the
OS lock, so threads in the same process serialize on the same path even
on platforms where same-process fd locking would be a no-op.

Windows limitation (documented, not silent): ``msvcrt.locking`` has no
shared/read lock mode, so :func:`shared_locked` **degrades to an
exclusive lock on Windows**. Readers block writers there. Code that needs
true concurrent readers must not rely on ``shared_locked`` on Windows.
"""
from __future__ import annotations

import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    import msvcrt
else:
    import fcntl

# Per-path in-process locks: threads in one process serialize here first,
# the OS lock then serializes across processes. Keyed by resolved path so
# "a/../b.lock" and "b.lock" share one lock.
_path_locks: dict[str, threading.RLock] = {}
_path_locks_guard = threading.Lock()


def _thread_lock(lock_path: Path) -> threading.RLock:
    key = str(lock_path.resolve())
    with _path_locks_guard:
        rl = _path_locks.get(key)
        if rl is None:
            rl = threading.RLock()
            _path_locks[key] = rl
        return rl


def _msvcrt():
    """The Windows locking backend, resolved late so tests can inject a
    fake ``msvcrt`` into ``sys.modules`` and execute the real Windows code
    path on any platform."""
    return sys.modules["msvcrt"]


@contextmanager
def locked(lock_path: str | Path):
    """Hold an exclusive cross-process lock on ``lock_path``.

    The lock file is created if missing. The same file must be used by
    every participant guarding a given resource.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock(lock_path):
        # "a+b" creates the file if missing without truncating it
        with open(lock_path, "a+b") as fh:
            _acquire(fh, exclusive=True)
            try:
                yield fh
            finally:
                _release(fh, exclusive=True)


@contextmanager
def shared_locked(lock_path: str | Path):
    """Hold a shared (read) cross-process lock on ``lock_path``.

    WARNING: on Windows this degrades to an EXCLUSIVE lock (see module
    docstring) — readers block writers there.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock(lock_path):
        with open(lock_path, "a+b") as fh:
            _acquire(fh, exclusive=False)
            try:
                yield fh
            finally:
                _release(fh, exclusive=False)


def _acquire(fh, exclusive: bool) -> None:
    if _IS_WINDOWS:
        msvcrt = _msvcrt()
        # LK_LOCK blocks until the 1-byte region is free; LK_UNLCK releases.
        # Lock the first byte; the file is at least 1 byte after "a+b" open
        # on an empty file? msvcrt needs the region to exist — ensure size.
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write(b"\x00")
            fh.flush()
        fh.seek(0)
        # No shared mode in msvcrt: shared degrades to exclusive (documented).
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)


def _release(fh, exclusive: bool) -> None:
    if _IS_WINDOWS:
        msvcrt = _msvcrt()
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

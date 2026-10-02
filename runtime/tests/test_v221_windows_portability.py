"""GATE 2 — Windows real execution / portability.

Guarantees:
  1. No unconditional top-level ``import fcntl`` anywhere in the runtime
     (it would break ``import skillhub`` on Windows outright).
  2. The *real Windows msvcrt code path* in filelock executes correctly —
     run here with an injected fake ``msvcrt`` that emulates mandatory
     1-byte-region locking with blocking ``LK_LOCK`` semantics. This is
     execution of the Windows branch, not an AST check.
  3. On the Windows path, ``shared_locked`` degrades to an exclusive lock
     (documented limitation) — proven by the fake recording ``LK_LOCK``.
  4. Per-path thread RLock serializes threads in one process.
  5. Multiprocessing races use the portable ``spawn`` start method, the
     only one Windows has (``fork`` contexts are banned in tests).
"""
from __future__ import annotations

import ast
import multiprocessing as mp
import sys
import threading
import types
from pathlib import Path

import pytest

from skillhub import filelock


# --- 1. no unconditional top-level import fcntl -------------------------------

def _top_level_imports(tree: ast.Module) -> list[str]:
    return [n.names[0].name for n in tree.body
            if isinstance(n, (ast.Import,)) ]


def test_no_unconditional_top_level_fcntl():
    pkg = Path(filelock.__file__).parent
    offenders = []
    for path in sorted(pkg.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name in _top_level_imports(tree):
            if name == "fcntl":
                offenders.append(str(path.relative_to(pkg)))
    assert offenders == [], f"unconditional top-level import fcntl: {offenders}"


def test_fcntl_msvcrt_imports_are_platform_guarded():
    src = Path(filelock.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    guarded = set()

    def visit(node, in_guard):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If):
                test_src = ast.dump(child.test)
                guard = "win32" in test_src or "_IS_WINDOWS" in test_src
                visit(child, in_guard or guard)
            elif isinstance(child, ast.Import):
                for a in child.names:
                    if a.name in ("fcntl", "msvcrt"):
                        assert in_guard, \
                            f"import {a.name} not platform-guarded"
                        guarded.add(a.name)
            else:
                visit(child, in_guard)

    visit(tree, False)
    assert guarded == {"fcntl", "msvcrt"}


# --- 2+3. execute the real Windows branch with an emulated msvcrt -----------

class FakeMsvcrt:
    """Emulates msvcrt.locking mandatory 1-byte-region semantics:
    LK_LOCK blocks until free, LK_UNLCK releases."""
    LK_LOCK = 1
    LK_UNLCK = 0

    def __init__(self):
        self.calls: list[tuple] = []
        self._region: dict[int, threading.Lock] = {}
        self._guard = threading.Lock()

    def locking(self, fd, mode, nbytes):
        self.calls.append((fd, mode, nbytes))
        with self._guard:
            region = self._region.setdefault(fd, threading.Lock())
        if mode == self.LK_LOCK:
            region.acquire()  # blocks, like the real LK_LOCK
        elif mode == self.LK_UNLCK:
            try:
                region.release()
            except RuntimeError:
                raise OSError("unlock of unlocked region")
        else:
            raise OSError(f"bad mode {mode}")


@pytest.fixture
def windows_filelock(monkeypatch):
    """Run filelock's Windows branch on this machine."""
    fake_mod = types.ModuleType("msvcrt")
    fake = FakeMsvcrt()
    fake_mod.LK_LOCK = fake.LK_LOCK
    fake_mod.LK_UNLCK = fake.LK_UNLCK
    fake_mod.locking = fake.locking
    monkeypatch.setitem(sys.modules, "msvcrt", fake_mod)
    monkeypatch.setattr(filelock, "_IS_WINDOWS", True)
    return fake


def test_windows_branch_exclusive_lock_executes(tmp_path, windows_filelock):
    """The real Windows _acquire/_release path runs: empty file gets the
    bootstrap byte, LK_LOCK is taken, LK_UNLCK released."""
    lock = tmp_path / "w.lock"
    with filelock.locked(lock):
        assert lock.stat().st_size >= 1  # bootstrap byte written
        modes = [c[1] for c in windows_filelock.calls]
        assert windows_filelock.LK_LOCK in modes
    modes = [c[1] for c in windows_filelock.calls]
    assert windows_filelock.LK_UNLCK in modes


def test_windows_branch_serializes_threads(tmp_path, windows_filelock):
    """Two threads racing locked() on the Windows branch → serialized
    counter, exactly like the Unix flock path."""
    counter = tmp_path / "ctr.txt"
    counter.write_text("0")
    lock = tmp_path / "w.lock"
    errors = []

    def worker(n):
        try:
            for _ in range(25):
                with filelock.locked(lock):
                    v = int(counter.read_text())
                    counter.write_text(str(v + 1))
        except Exception as exc:  # surfaced, never swallowed
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert not errors
    assert not any(t.is_alive() for t in threads)
    assert counter.read_text() == "100"


def test_windows_shared_lock_degrades_to_exclusive(tmp_path,
                                                   windows_filelock):
    """Documented limitation, proven: shared_locked() issues LK_LOCK
    (exclusive) on the Windows branch — readers block writers."""
    lock = tmp_path / "s.lock"
    with filelock.shared_locked(lock):
        pass
    modes = [c[1] for c in windows_filelock.calls]
    assert windows_filelock.LK_LOCK in modes, \
        "Windows shared lock must degrade to exclusive LK_LOCK"


# --- 4. per-path thread RLock -------------------------------------------------

def test_thread_rlock_serializes_same_path(tmp_path):
    counter = tmp_path / "t.txt"
    counter.write_text("0")
    lock = tmp_path / "t.lock"

    def worker():
        for _ in range(50):
            with filelock.locked(lock):
                v = int(counter.read_text())
                counter.write_text(str(v + 1))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert counter.read_text() == "400"


def test_thread_rlock_is_per_path_and_reentrant(tmp_path):
    a = tmp_path / "a.lock"
    b = tmp_path / "b.lock"
    assert filelock._thread_lock(a) is filelock._thread_lock(a)
    assert filelock._thread_lock(a) is not filelock._thread_lock(b)
    rl = filelock._thread_lock(a)
    assert rl.acquire(blocking=False)
    assert rl.acquire(blocking=False)  # RLock: same thread re-enters
    rl.release()
    rl.release()


# --- 5. spawn is the only allowed start method in tests -----------------------

def test_spawn_context_is_portable():
    ctx = mp.get_context("spawn")
    assert ctx._name == "spawn"


def test_no_fork_context_in_tests():
    tests_dir = Path(__file__).parent
    offenders = []
    for path in sorted(tests_dir.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue  # this file only mentions fork to ban it
        src = path.read_text(encoding="utf-8")
        if 'get_context("fork")' in src or "get_context('fork')" in src:
            offenders.append(path.name)
    assert offenders == [], f"fork-based races (break on Windows): {offenders}"


# --- 6. EDEADLK backoff (GATE 20 CI finding) -----------------------------------
#
# windows-latest/py3.10, 20 racing processes: the CRT reported EDEADLK
# ("Resource deadlock avoided") for the 1-byte region when our own process
# had just released it on a previous handle (OS lock teardown races the
# next acquisition). _acquire must ride it out with a bounded backoff
# instead of dying; genuine errors must still surface.

import errno  # noqa: E402  (kept with the other stdlib imports above)


class FlakyMsvcrt(FakeMsvcrt):
    """FakeMsvcrt that raises spurious EDEADLK on the first `flakes`
    LK_LOCK calls, then behaves normally."""

    def __init__(self, flakes: int):
        super().__init__()
        self._flakes = flakes
        self.attempts = 0

    def locking(self, fd, mode, nbytes):
        if mode == self.LK_LOCK:
            self.attempts += 1
            if self._flakes > 0:
                self._flakes -= 1
                raise OSError(errno.EDEADLK, "Resource deadlock avoided")
        return super().locking(fd, mode, nbytes)


@pytest.fixture
def flaky_windows_filelock(monkeypatch):
    """Windows branch with a fake msvcrt that spuriously reports EDEADLK."""
    fake_mod = types.ModuleType("msvcrt")
    fake = FlakyMsvcrt(flakes=25)
    fake_mod.LK_LOCK = fake.LK_LOCK
    fake_mod.LK_UNLCK = fake.LK_UNLCK
    fake_mod.locking = fake.locking
    monkeypatch.setitem(sys.modules, "msvcrt", fake_mod)
    monkeypatch.setattr(filelock, "_IS_WINDOWS", True)
    return fake


def test_windows_edeadlk_backoff_rides_out_spurious_deadlock(
    tmp_path, flaky_windows_filelock
):
    """25 spurious EDEADLKs are absorbed; the lock is still acquired and
    released exactly once."""
    lock = tmp_path / "flaky.lock"
    with filelock.locked(lock):
        pass
    assert flaky_windows_filelock.attempts == 26  # 25 flakes + 1 real acquire
    assert flaky_windows_filelock._flakes == 0  # every flake was consumed
    unlocks = [c for c in flaky_windows_filelock.calls if c[1] == 0]
    assert len(unlocks) == 1


def test_windows_edeadlk_eventually_raises(tmp_path, monkeypatch):
    """A *persistent* EDEADLK (genuine nested-lock bug) still surfaces
    instead of hanging forever — retries are bounded (~2s here)."""

    class AlwaysDeadlocked(FakeMsvcrt):
        def locking(self, fd, mode, nbytes):
            if mode == self.LK_LOCK:
                raise OSError(errno.EDEADLK, "Resource deadlock avoided")
            return super().locking(fd, mode, nbytes)

    fake_mod = types.ModuleType("msvcrt")
    fake = AlwaysDeadlocked()
    fake_mod.LK_LOCK = fake.LK_LOCK
    fake_mod.LK_UNLCK = fake.LK_UNLCK
    fake_mod.locking = fake.locking
    monkeypatch.setitem(sys.modules, "msvcrt", fake_mod)
    monkeypatch.setattr(filelock, "_IS_WINDOWS", True)
    with pytest.raises(OSError, match="Resource deadlock avoided"):
        with filelock.locked(tmp_path / "stuck.lock"):
            pass  # pragma: no cover


def test_windows_other_oserror_not_masked(tmp_path, monkeypatch):
    """A non-EDEADLK OSError (e.g. permission denied) propagates
    immediately — the backoff must not swallow real failures."""

    class Denied(FakeMsvcrt):
        def locking(self, fd, mode, nbytes):
            if mode == self.LK_LOCK:
                self.attempts = getattr(self, "attempts", 0) + 1
                raise OSError(errno.EACCES, "Permission denied")
            return super().locking(fd, mode, nbytes)

    fake_mod = types.ModuleType("msvcrt")
    fake = Denied()
    fake_mod.LK_LOCK = fake.LK_LOCK
    fake_mod.LK_UNLCK = fake.LK_UNLCK
    fake_mod.locking = fake.locking
    monkeypatch.setitem(sys.modules, "msvcrt", fake_mod)
    monkeypatch.setattr(filelock, "_IS_WINDOWS", True)
    with pytest.raises(OSError, match="Permission denied"):
        with filelock.locked(tmp_path / "denied.lock"):
            pass  # pragma: no cover
    assert fake.attempts == 1  # no retries on non-EDEADLK

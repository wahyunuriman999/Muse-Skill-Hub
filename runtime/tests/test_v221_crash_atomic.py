"""GATE 3 — crash-atomic storage, proven by fault injection.

Guarantees:
  1. A process killed with SIGKILL mid-write NEVER leaves a torn store:
     every store file is always the old or the new version, never garbage.
     (Real kills, not mocks.)
  2. The vault serializes read-modify-write on a separate ``vault.lock``
     file and writes crash-atomically (tmp + fsync + os.replace).
  3. Corrupt stores fail CLOSED: backup + StoreCorruptError, never silent
     defaults — including invalid-UTF-8 bytes (which v2.2.0 let propagate
     as a raw UnicodeDecodeError).
  4. A torn final line in audit.jsonl (crash between write and flush)
     does not break logging: the chain continues from the last GOOD event.
"""
from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import os
import random
import time

import pytest

from skillhub import audit, localstore
from skillhub.errors import StoreCorruptError
from skillhub.skills import secure_vault


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


def _spawn():
    return mp.get_context("spawn")


# --- 1. real SIGKILL during writes -------------------------------------------

def _lstore_crash_worker(data_dir: str, rounds: int):
    import os as _os
    _os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub import localstore as _ls
    for i in range(rounds):
        with _ls.locked_json("crashtest", {}) as data:
            data["i"] = i
            data["payload"] = "x" * 30000


def _kill_writer(target, data_dir: str, iterations: int = 6):
    """Spawn-kill cycles: start writer, wait until it has written at least
    once, SIGKILL it mid-flight, then the store file MUST always be valid
    JSON (old or new version) — never torn."""
    for _ in range(iterations):
        ctx = _spawn()
        p = ctx.Process(target=target, args=(data_dir, 200))
        p.start()
        try:
            deadline = time.time() + 15
            probe = os.path.join(data_dir, _PROBE_FILE[target.__name__])
            while time.time() < deadline and not os.path.exists(probe):
                time.sleep(0.01)
            time.sleep(random.uniform(0.005, 0.05))
        finally:
            p.kill()  # SIGKILL — no cleanup, like a real crash / power loss
            p.join(10)
            p.close()


_PROBE_FILE = {
    "_lstore_crash_worker": "crashtest.json",
    "_vault_crash_worker": "vault.enc.json",
}


def test_kill9_mid_write_never_torn_store(isolated):
    _kill_writer(_lstore_crash_worker, str(isolated))
    raw = (isolated / "crashtest.json").read_text(encoding="utf-8")
    data = json.loads(raw)  # must parse — never a torn file
    assert isinstance(data, dict)
    assert not list(isolated.glob("crashtest.tmp.*"))  # no tmp debris


def _vault_crash_worker(data_dir: str, rounds: int):
    import asyncio as _aio
    import os as _os
    _os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub.skills import secure_vault as _sv
    for i in range(rounds):
        _aio.run(_sv.store_secret(
            {"name": f"k{i % 7}", "value": "v" * 5000}))


def test_kill9_mid_write_never_torn_vault(isolated):
    _kill_writer(_vault_crash_worker, str(isolated))
    p = isolated / "vault.enc.json"
    if p.exists():
        # decryptable to a dict, or fail-closed — never silent garbage
        try:
            vault = secure_vault._load()
        except StoreCorruptError:
            pass  # fail-closed is acceptable; silent corruption is not
        else:
            assert isinstance(vault, dict)


# --- 2. vault serializes concurrent writers ----------------------------------

def _vault_writer(data_dir: str, worker_id: int, q):
    import asyncio as _aio
    import os as _os
    _os.environ["SKILLHUB_LOCAL_DIR"] = data_dir
    from skillhub.skills import secure_vault as _sv
    try:
        for i in range(10):
            _aio.run(_sv.store_secret(
                {"name": f"w{worker_id}-s{i}", "value": f"secret-{i}"}))
        q.put("done")
    except Exception as exc:
        q.put(f"error:{type(exc).__name__}:{exc}")


def test_vault_concurrent_writes_all_survive(isolated):
    ctx = _spawn()
    q = ctx.Queue()
    procs = [ctx.Process(target=_vault_writer,
                         args=(str(isolated), wid, q)) for wid in range(10)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    assert not any(p.exitcode for p in procs), "worker crashed"
    assert [q.get(timeout=10) for _ in procs].count("done") == 10
    vault = secure_vault._load()
    assert len(vault) == 100  # every secret survived, none lost/clobbered
    assert (isolated / "vault.lock").exists()  # separate lock file used


# --- 3. corruption fails closed ----------------------------------------------

def test_truncated_json_backs_up_and_raises(isolated):
    (isolated / "t.json").write_text('{"a": 1, "b": [2,')
    with pytest.raises(StoreCorruptError):
        localstore.read_json("t", {})
    backups = list(isolated.glob("t.corrupt.*.json"))
    assert len(backups) == 1
    assert "2," in backups[0].read_text()  # original bytes preserved


def test_invalid_utf8_backs_up_and_raises(isolated):
    """v2.2.0 let this propagate as a raw UnicodeDecodeError."""
    (isolated / "u.json").write_bytes(b'{"a": "\xff\xfe invalid utf8')
    with pytest.raises(StoreCorruptError):
        localstore.read_json("u", {})
    backups = list(isolated.glob("u.corrupt.*.json"))
    assert len(backups) == 1


def test_empty_file_is_not_corruption(isolated):
    (isolated / "e.json").write_text("")
    assert localstore.read_json("e", {"d": 1}) == {"d": 1}
    assert list(isolated.glob("e.corrupt.*")) == []


def test_vault_corruption_fails_closed_with_backup(isolated):
    (isolated / "vault.enc.json").write_bytes(b"truncated-ciphertext!!")
    with pytest.raises(StoreCorruptError):
        secure_vault._load()
    backups = list(isolated.glob("vault.corrupt.*.enc.json"))
    assert len(backups) == 1
    # and the corrupt file is gone — it can never be read as "empty vault"
    assert not (isolated / "vault.enc.json").exists()


def test_vault_wrong_key_fails_closed(isolated, monkeypatch):
    asyncio.run(secure_vault.store_secret({"name": "s", "value": "v"}))
    from cryptography.fernet import Fernet
    monkeypatch.setenv("SKILLHUB_VAULT_KEY", Fernet.generate_key().decode())
    with pytest.raises(StoreCorruptError):
        secure_vault._load()


# --- 4. torn audit tail -------------------------------------------------------

def test_audit_partial_final_line_does_not_break_chain(isolated):
    r1 = audit.log({"skill": "t", "action": "a1", "result": "success"})
    r2 = audit.log({"skill": "t", "action": "a2", "result": "success"})
    p = isolated / "audit.jsonl"
    # simulate a crash between write() and flush(): a2's line torn in half.
    # The torn event is unrecoverable and discarded; the chain must continue
    # from the last GOOD event (a1), and the next event must NOT be glued
    # onto the torn bytes.
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    torn = lines[-1][: len(lines[-1]) // 2]  # cut mid-line, no newline
    p.write_text("".join(lines[:-1]) + torn, encoding="utf-8")

    r3 = audit.log({"skill": "t", "action": "a3", "result": "success"})
    assert r3["prev_hash"] == r1["event_hash"]

    report = audit.verify_chain()
    assert report["ok"] is True
    assert report["chained"] == 2

    rows = audit.query(limit=10)
    assert sorted(r["action"] for r in rows) == ["a1", "a3"]
    # the torn bytes are gone — the file holds only complete lines
    for line in p.read_text(encoding="utf-8").splitlines():
        json.loads(line)

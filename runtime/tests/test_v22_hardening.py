"""v2.2 hardening tests — proving the third audit's P0/P1 items.

Covers: cross-platform file locking (no top-level fcntl), crash-atomic
stores (tmp+fsync+replace under a separate lock file), multi-PROCESS races
for approval consumption and idempotency reservation (the documented
guarantee is about processes, not threads), OAuth single-flight refresh,
fail-closed credential store, approval param privacy, the standard
jsonschema library (full Draft 2020-12 vocabulary), declared
cryptography/jsonschema dependencies, generated README metrics, and the
destructive-risk security conformance check.
"""

import ast
import json
import multiprocessing as mp


def _spawn():
    """Portable process context: Windows/macOS only HAVE spawn; Linux
    defaults to fork. GATE 2 forces spawn everywhere so the race tests
    execute the same code path on every OS."""
    return mp.get_context("spawn")

import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from skillhub import approval, localstore, registry
from skillhub.errors import (CredentialStoreCorruptError, IdempotencyConflict,
                             InvalidInput)

RUNTIME = Path(__file__).resolve().parent.parent


@pytest.fixture()
def local_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


# --- cross-platform locking ----------------------------------------------------
def test_no_top_level_fcntl_import():
    """The v2.1 audit's Windows P0: `import fcntl` at module top level breaks
    every import chain on Windows. Only filelock.py may touch fcntl/msvcrt,
    and only behind a platform guard."""
    pkg = RUNTIME / "skillhub"
    offenders = []
    for py in sorted(pkg.glob("*.py")):
        if py.name == "filelock.py":
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name == "fcntl" for a in node.names):
                    offenders.append(f"{py.name}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "fcntl":
                    offenders.append(f"{py.name}:{node.lineno}")
    assert not offenders, f"top-level fcntl imports: {offenders}"


def test_filelock_module_has_platform_branches():
    from skillhub import filelock
    src = Path(filelock.__file__).read_text(encoding="utf-8")
    assert "msvcrt" in src and "fcntl" in src
    assert filelock.platform_name() in ("unix", "windows")
    expected = "windows" if sys.platform == "win32" else "unix"
    assert filelock.platform_name() == expected  # must match the real platform


def _lock_counter_worker(lock_path, counter_path, n, q):
    from skillhub import filelock
    for _ in range(n):
        with filelock.locked(lock_path):
            v = int(Path(counter_path).read_text() or "0")
            # widen the race window so a missing lock would actually lose
            time.sleep(0.001)
            Path(counter_path).write_text(str(v + 1))
    q.put("done")


def test_filelock_exclusive_across_processes(tmp_path):
    """20 processes x 50 increments under the lock → exactly 1000."""
    lock_path = str(tmp_path / "ctr.lock")
    counter_path = str(tmp_path / "ctr.txt")
    Path(counter_path).write_text("0")
    ctx = _spawn()
    q = ctx.Queue()
    procs = [ctx.Process(target=_lock_counter_worker,
                         args=(lock_path, counter_path, 50, q))
             for _ in range(20)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    assert [q.get(timeout=10) for _ in procs].count("done") == 20
    assert not any(p.exitcode for p in procs)
    assert Path(counter_path).read_text() == "1000"


# --- multi-process approval race ------------------------------------------------
def _consume_worker(aid, q):
    from skillhub import approval as ap
    from skillhub.errors import ApprovalRevoked
    try:
        ap.consume(aid, "s", "a", {"x": 1}, "write", actor="local-user")
        q.put("win")
    except ApprovalRevoked:
        q.put("loss")
    except Exception as exc:  # pragma: no cover - surfaced explicitly
        q.put(f"error:{type(exc).__name__}:{exc}")


def test_approval_consume_is_atomic_across_processes(local_dir):
    """The documented guarantee: two concurrent PROCESSES cannot both
    consume the same approval. 20 processes → exactly 1 winner."""
    item = approval.request_approval("s", "a", {"x": 1}, risk="write")
    approval.approve(item["approval_id"])
    aid = item["approval_id"]
    ctx = _spawn()
    q = ctx.Queue()
    procs = [ctx.Process(target=_consume_worker, args=(aid, q))
             for _ in range(20)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    assert not any(p.exitcode for p in procs), "worker crashed"
    results = [q.get(timeout=10) for _ in procs]
    assert results.count("win") == 1, results
    assert results.count("loss") == 19, results
    assert approval.get(aid)["status"] == "consumed"


# --- multi-process idempotency race ----------------------------------------------
def _reserve_worker(key, q):
    from skillhub.registry import _idem_reserve
    try:
        owned, _ = _idem_reserve(key, "s", "a", "ph")
        q.put("owned" if owned else "denied")
    except Exception as exc:  # pragma: no cover - surfaced explicitly
        q.put(f"error:{type(exc).__name__}:{exc}")


def test_idempotency_reserve_is_atomic_across_processes(local_dir):
    key = "idem-p22"
    ctx = _spawn()
    q = ctx.Queue()
    procs = [ctx.Process(target=_reserve_worker, args=(key, q))
             for _ in range(20)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(60)
    assert not any(p.exitcode for p in procs), "worker crashed"
    results = [q.get(timeout=10) for _ in procs]
    assert results.count("owned") == 1, results
    assert results.count("denied") == 19, results


# --- crash-atomic stores ----------------------------------------------------------
def test_locked_json_write_is_crash_atomic(local_dir):
    """locked_json writes via tmp+fsync+os.replace: no tmp debris remains
    and the file is always whole."""
    with localstore.locked_json("atomic", {}) as data:
        data["k"] = "v" * 10000
    leftovers = list(local_dir.glob("atomic.tmp.*"))
    assert leftovers == []
    assert json.loads((local_dir / "atomic.json").read_text()) == {
        "k": "v" * 10000}


def test_locked_json_uses_separate_lock_file(local_dir):
    with localstore.locked_json("seplock", {}) as data:
        data["a"] = 1
    assert (local_dir / "seplock.lock").exists()
    assert (local_dir / "seplock.json").exists()


def test_write_atomic_leaves_either_old_or_new(local_dir):
    """Direct _write_atomic: file content is always parseable JSON."""
    from skillhub.localstore import _path, _write_atomic
    _write_atomic(_path("w"), {"n": 1})
    _write_atomic(_path("w"), {"n": 2})
    assert json.loads((local_dir / "w.json").read_text()) == {"n": 2}
    assert list(local_dir.glob("w.json.tmp.*")) == []


# --- credential store: fail-closed + crash-atomic ----------------------------------
def test_credential_store_fail_closed_on_corruption(local_dir):
    from skillhub import credentials
    credentials.save_local("K", "v")
    enc = local_dir / "credentials.enc"
    assert enc.exists()
    enc.write_bytes(b"definitely not a fernet token")
    with pytest.raises(CredentialStoreCorruptError):
        credentials._read_store()
    backups = list(local_dir.glob("credentials.corrupt.*.enc"))
    assert len(backups) == 1


def test_credential_store_missing_file_is_empty_not_error(local_dir):
    from skillhub import credentials
    assert credentials._read_store() == {}


def test_credential_store_write_is_crash_atomic(local_dir):
    from skillhub import credentials
    credentials.save_local("A", "1")
    credentials.save_local("B", "2")
    assert list(local_dir.glob("credentials.enc.tmp.*")) == []
    assert credentials._read_store()["B"]["value"] == "2"


# --- OAuth single-flight ------------------------------------------------------------
def test_oauth_refresh_single_flight(local_dir, monkeypatch):
    """20 threads racing an expired token → exactly ONE refresh request;
    everyone gets the winner's rotated token."""
    from skillhub import credentials, oauth
    calls = []

    def fake_refresh(oauth_meta, skill):
        calls.append(1)
        time.sleep(0.05)  # widen the race window
        n = len(calls)
        return {"access_token": f"tok-{n}",
                "refresh_token": f"ref-{n}",
                "expires_at": int(time.time()) + 3600}

    monkeypatch.setattr(oauth, "_refresh", fake_refresh)
    oauth.save_oauth("O", access_token="old", refresh_token="r0",
                     client_id="c", client_secret="s",
                     token_url="https://x/token",
                     expires_at=int(time.time()) - 10)
    results, errors = [], []

    def worker():
        try:
            results.append(credentials.cred("O", skill="t"))
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert not errors, errors
    assert len(calls) == 1, f"expected single-flight, got {len(calls)} refreshes"
    assert set(results) == {"tok-1"}, results
    # rotated refresh token persisted
    rec = credentials._read_store()["O"]
    assert rec["oauth"]["refresh_token"] == "ref-1"


# --- approval param privacy ------------------------------------------------------------
def test_approval_store_does_not_persist_raw_params(local_dir):
    item = approval.request_approval(
        "gmail", "send_message",
        {"to": "a@b.c", "subject": "hi", "body": "super secret body",
         "password": "hunter2"},
        risk="communication")
    stored = approval.get(item["approval_id"])
    assert "params" not in stored, "raw params must not be persisted"
    assert stored["params_hash"]  # binding hash still present
    preview = stored["params_preview"]
    assert preview["to"] == "a@b.c"  # non-sensitive preview kept (audit policy)
    assert preview.get("password") == "[redacted]"
    # preview follows the audit log's redaction policy: secret KEYS are
    # redacted, other values appear truncated — never the full raw dict
    assert set(preview) == {"to", "subject", "body", "password"}
    # execution still works: caller re-supplies params, hash is verified
    approval.approve(item["approval_id"])
    consumed = approval.consume(item["approval_id"], "gmail", "send_message",
                                {"to": "a@b.c", "subject": "hi",
                                 "body": "super secret body",
                                 "password": "hunter2"}, "communication")
    assert consumed["status"] == "consumed"


# --- standard jsonschema library ---------------------------------------------------------
def test_jsonschema_full_vocabulary_ref_and_conditionals():
    from skillhub.validate import validate_output, validate_params
    params = {
        "$defs": {
            "user": {"type": "object",
                     "properties": {"name": {"type": "string"}},
                     "required": ["name"]}
        },
        "user": {"$ref": "#/$defs/user"},
        "contact": {
            "type": "object",
            "properties": {
                "kind": {"enum": ["email", "phone"]},
                "value": {"type": "string"},
            },
            # if kind=email then value must look like an email
            "if": {"properties": {"kind": {"const": "email"}}},
            "then": {"properties": {"value": {"format": "email"}}},
        },
    }
    good = {"user": {"name": "Wahyu"},
            "contact": {"kind": "email", "value": "a@b.c"}}
    validate_params("s", "a", params, [], good, strict=True)
    with pytest.raises(InvalidInput):  # $ref target violated
        validate_params("s", "a", params, [], {"user": {"name": 1}},
                        strict=True)
    with pytest.raises(InvalidInput):  # if/then violated
        validate_params("s", "a", params, [],
                        {"contact": {"kind": "email", "value": "nope"}},
                        strict=True)
    # dependentRequired at the object level — real Draft 2020-12 keyword
    schema = {
        "type": "object",
        "properties": {"credit_card": {"type": "string"},
                       "billing_address": {"type": "string"}},
        "dependentRequired": {"credit_card": ["billing_address"]},
    }
    validate_output("s", "a", schema,
                    {"credit_card": "123", "billing_address": "x"})
    with pytest.raises(Exception):
        validate_output("s", "a", schema, {"credit_card": "123"})


def test_jsonschema_contains_and_propertynames():
    from skillhub.validate import validate_output
    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array",
                     "contains": {"type": "string", "pattern": "^urgent"}},
            "meta": {"type": "object", "propertyNames": {"pattern": "^x-"}},
        },
        "required": ["tags"],
    }
    validate_output("s", "a", schema,
                    {"tags": ["urgent-fix", "low"], "meta": {"x-a": 1}})
    with pytest.raises(Exception):  # contains violated
        validate_output("s", "a", schema, {"tags": ["low"]})
    with pytest.raises(Exception):  # propertyNames violated
        validate_output("s", "a", schema,
                        {"tags": ["urgent"], "meta": {"bad": 1}})


# --- declared dependencies --------------------------------------------------------------
def test_cryptography_and_jsonschema_are_declared_dependencies():
    req = (RUNTIME / "requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"^cryptography>=", req, re.M), "cryptography missing"
    assert re.search(r"^jsonschema>=", req, re.M), "jsonschema missing"
    pyproject = (RUNTIME / "pyproject.toml").read_text(encoding="utf-8")
    assert '"cryptography>=' in pyproject
    assert '"jsonschema>=' in pyproject


# --- destructive-risk conformance -----------------------------------------------------------
def test_destructive_named_actions_are_approval_gated():
    """Mirrors the `skillhub validate` check: a destructive name with plain
    'write' risk would allow bare confirm=true — forbidden."""
    reg = registry.load_registry()
    bad = []
    for sname, entry in reg.items():
        for aname, ad in entry.actions.items():
            n = aname.lower()
            destructive = any(v in n for v in (
                "delete", "destroy", "revoke", "terminate", "purge", "wipe"))
            destructive = destructive or n.startswith("remove_") \
                or n.endswith("_delete")
            if destructive and ad.risk == "write":
                bad.append(f"{sname}.{aname}")
    assert not bad, f"destructive actions with risk=write: {bad}"


# --- generated README metrics -----------------------------------------------------------------
def test_readme_metrics_in_sync():
    """READMEs carry a generated metrics block; fail if it drifted."""
    r = subprocess.run(
        [sys.executable, "tools/sync_readme.py", "--check"],
        cwd=RUNTIME, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, (
        "README metrics out of sync — run python tools/sync_readme.py\n"
        + r.stdout + r.stderr)

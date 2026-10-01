"""GATE 17 — dependency/supply-chain audit.

  1. the committed DEPENDENCY_AUDIT.md is in sync with pyproject
     (drift-checked, no network needed);
  2. the artifact records a clean run: pip check clean AND pip-audit
     reporting 0 vulnerabilities (the artifact is the evidence; the live
     scan itself needs the OSV database and is re-run via --audit);
  3. findings are attributed per group — a toolchain CVE can never be
     mistaken for a project CVE;
  4. pip check passes in the current environment (no broken requirements).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME = ROOT / "runtime"


def test_dependency_audit_in_sync():
    r = subprocess.run(
        [sys.executable, "tools/dependency_audit.py", "--check"],
        cwd=RUNTIME, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, \
        "dependency audit out of sync — run: " \
        "python tools/dependency_audit.py --audit\n" + r.stdout + r.stderr


def test_audit_records_clean_scan():
    text = (ROOT / "certification" / "DEPENDENCY_AUDIT.md").read_text(
        encoding="utf-8")
    assert "**0 known vulnerabilities**" in text
    assert "pip check:** clean" in text
    for group in ("project dependencies", "test dependencies", "toolchain"):
        assert group in text, f"missing group section: {group}"


def test_audit_lists_declared_project_deps():
    text = (ROOT / "certification" / "DEPENDENCY_AUDIT.md").read_text(
        encoding="utf-8")
    for spec in ("mcp>=1.0,<2", "httpx>=0.27", "pyyaml>=6.0",
                 "cryptography>=41", "jsonschema>=4.18"):
        assert f"`{spec}`" in text, f"declared dep missing: {spec}"
    # the wheel ships only the project group — the artifact says so
    assert "never reach users" in text


def test_pip_check_clean():
    r = subprocess.run([sys.executable, "-m", "pip", "check"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, "pip check failed:\n" + r.stdout + r.stderr

"""GATE 13 — static security audit.

An independent AST-based audit (``tools/static_audit.py``, stdlib only,
no reuse of the validator's patterns) scans every driver. Proven here:
  1. the audit passes on the tree: 0 HIGH findings;
  2. the audit is not vacuous: planted shell=True / os.system /
     eval-on-input / hardcoded-secret snippets are all flagged HIGH;
  3. the broad ``facebook-cli run_command`` argv passthrough is typed
     ``destructive`` (driver-declared, manifest-confirmed) and a dispatch
     without an approval_id raises ApprovalRequired — bare confirm=True
     is not enough;
  4. the taint analysis distinguishes full argv passthrough
     (facebook-cli, caller picks flags) from driver-composed argv
     (magic-moment, fixed ffmpeg binary, exec-style).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RUNTIME / "tools"))
import static_audit
from static_audit import audit_tree  # noqa: E402

from skillhub.errors import ApprovalRequired  # noqa: E402
from skillhub.registry import dispatch, load_registry  # noqa: E402


def _high(findings):
    return [f for f in findings if f.severity == "HIGH"]


def test_audit_passes_on_tree():
    findings = audit_tree(RUNTIME)
    assert _high(findings) == [], \
        "\n".join(str(f) for f in _high(findings))


def test_audit_is_not_vacuous(tmp_path):
    vuln = tmp_path / "skillhub" / "skills"
    vuln.mkdir(parents=True)
    (vuln / "evil.py").write_text(
        "import os, subprocess\n"
        "API_KEY = 'sk-live-0123456789abcdef'\n"
        "def h(params):\n"
        "    subprocess.run('ls ' + params['d'], shell=True)\n"
        "    os.system('rm -rf ' + params['d'])\n"
        "    return eval(params['expr'])\n",
        encoding="utf-8")
    findings = audit_tree(tmp_path)
    high = _high(findings)
    whats = " ".join(f.what for f in high)
    assert "shell=True" in whats
    assert "os.system" in whats
    assert "eval()" in whats
    assert "hardcoded secret" in whats


def test_facebook_cli_passthrough_requires_approval():
    reg = load_registry()
    entry = reg["facebook-cli"]
    ad = entry.actions["run_command"]
    # driver-declared (explicit), not a hand-tuned manifest override
    assert ad.risk_explicit and ad.risk == "destructive"
    # shipped manifest agrees: approval-gated
    text = (RUNTIME / "skillhub" / "catalog" / "facebook-cli"
            / "manifest.yaml").read_text(encoding="utf-8")
    assert "risk: destructive" in text
    assert "approval: required" in text


@pytest.mark.asyncio
async def test_facebook_cli_dispatch_without_approval_fails():
    reg = load_registry()
    with pytest.raises(ApprovalRequired):
        await dispatch(reg["facebook-cli"], "run_command",
                       {"args": ["post", "--help"]}, confirm=True)


def test_taint_kinds_distinguished():
    findings = audit_tree(RUNTIME)
    infos = " ".join(f.what for f in findings if f.severity == "INFO")
    assert "full argv passthrough in facebook-cli.run_command" in infos
    assert "driver-composed argv in magic-moment._run" in infos

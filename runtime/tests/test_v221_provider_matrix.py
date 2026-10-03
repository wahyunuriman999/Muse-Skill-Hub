"""GATE 15 — provider contract matrix.

Every implemented driver gets an honest evidence tier, regenerated from
ground truth (not docs):
  1. the committed matrix matches a fresh regeneration (--check);
  2. the live set is exactly {github, podcast} and each named live test
     function still exists in the suite;
  3. stripe has mock-contract evidence (request shape + response parsing
     against a mock responder, real driver code unmodified);
  4. there is no skill named `itunes` (the skill is `podcast`; the iTunes
     Search API is its provider);
  5. all 94 implemented drivers are classified and the tiers add up;
  6. no doc claims live provider testing beyond the live set.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME = ROOT / "runtime"

sys.path.insert(0, str(RUNTIME / "tools"))
from provider_matrix import LIVE_TESTS, build_matrix  # noqa: E402

from skillhub.registry import load_registry  # noqa: E402


def test_matrix_in_sync():
    r = subprocess.run(
        [sys.executable, "tools/provider_matrix.py", "--check"],
        cwd=RUNTIME, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, \
        "provider matrix out of sync — run python tools/provider_matrix.py\n" \
        + r.stdout + r.stderr


def test_live_set_is_exactly_github_and_podcast():
    assert set(LIVE_TESTS) == {"github", "podcast"}
    test_fns: set[str] = set()
    for path in (RUNTIME / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        test_fns.update(re.findall(r"^(?:async )?def (test_\w+)\(", text, re.M))
    for skill, fn in LIVE_TESTS.items():
        assert fn in test_fns, f"live test {fn} ({skill}) missing"


def test_stripe_has_mock_contract():
    rows = dict((n, t) for n, t, _ in build_matrix())
    assert rows["stripe"] == "mock-contract"
    text = (RUNTIME / "tests" / "test_provider_contracts.py").read_text(
        encoding="utf-8")
    assert 'mock_harness.register("stripe"' in text


def test_no_itunes_skill():
    reg = load_registry()
    assert "itunes" not in reg
    assert "podcast" in reg
    for path in (RUNTIME / "skillhub").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "itunes" not in text.lower() or "iTunes Search API" in text, \
            f"stale itunes reference in {path}"


def test_all_drivers_classified():
    reg = load_registry()
    rows = build_matrix()
    implemented = sorted(n for n, e in reg.items() if e.implemented)
    assert [n for n, _, _ in rows] == implemented
    assert len(rows) == 96
    tiers = [t for _, t, _ in rows]
    assert tiers.count("live") == 2
    assert tiers.count("mock-contract") == 3  # stripe + lovable + replit (v2.3)
    assert tiers.count("structural") == 91


def test_no_inflated_live_claims_in_docs():
    live = set(LIVE_TESTS)
    for readme in (ROOT / "README.md", RUNTIME / "README.md",
                   ROOT / "certification" / "PROVIDER_MATRIX.md"):
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        for m in re.finditer(r"live[\s-]test(?:ed|ing)?[^`\n]*`([\w-]+)`",
                             text, re.I):
            assert m.group(1) in live, \
                f"{readme}: inflated live claim for '{m.group(1)}'"

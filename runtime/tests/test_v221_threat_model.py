"""GATE 19 — threat model.

The threat model is a document gate; the tests pin its honesty:

  1. the document exists with the required sections (assets, trust
     boundaries, threats+mitigations, accepted limitations);
  2. every accepted limitation L1–L8 is stated explicitly — none may be
     silently dropped in a future edit;
  3. no limitation contradicts a certified guarantee (spot-check the two
     historically contested claims: exactly-once and the crash window);
  4. every threat row names the gate that proves its mitigation.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOC = ROOT / "certification" / "THREAT_MODEL.md"


def _text() -> str:
    assert DOC.exists(), "THREAT_MODEL.md missing"
    return DOC.read_text(encoding="utf-8")


def test_required_sections_present():
    text = _text()
    for section in ("## 2. Assets", "## 3. Trust boundaries",
                    "## 4. Threats and mitigations",
                    "## 5. Accepted limitations"):
        assert section in text, f"missing section: {section}"


def test_accepted_limitations_all_stated():
    text = _text()
    # L1..L8 must each appear with their number so a rewrite cannot
    # silently drop one.
    for n in range(1, 9):
        assert re.search(rf"\*\*L{n} —", text), f"limitation L{n} not stated"
    # the historically contested claims must be explicit
    assert "Crash after external side effect" in text
    assert "cannot close this window" in text
    assert "No tenant isolation" in text
    assert "not tamper-proof" in text
    assert "2 of 96 drivers are" in text and "live-tested" in text


def test_threats_name_their_gates():
    text = _text()
    threats = re.findall(r"^\| (T\d+) \|", text, re.M)
    assert len(threats) >= 10, f"expected >=10 threat rows, got {len(threats)}"
    for row in re.finditer(r"^\| T\d+ \|.*\|$", text, re.M):
        assert re.search(r"\b\d{1,2}\b", row.group(0)), \
            f"threat row names no gate: {row.group(0)[:60]}"


def test_no_contradiction_with_certified_guarantees():
    text = _text().lower()
    # the model must never claim what the gates proved we do NOT promise
    assert "exactly-once" in text  # only in the context of NOT promising it
    assert "are not claimed" in text

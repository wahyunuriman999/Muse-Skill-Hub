"""GATE 18 — performance sanity: measurements only, no guarantees.

  1. the committed PERF_SANITY.md lists every measured operation and
     carries the no-guarantees disclaimer (drift-checked);
  2. the measurement functions themselves run correctly (smoke check);
  3. nothing here asserts a latency bound — asserting one would invent a
     guarantee the project does not make.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME = ROOT / "runtime"

sys.path.insert(0, str(RUNTIME / "tools"))
from perf_sanity import _do_check, measure  # noqa: E402


def test_perf_artifact_in_sync():
    assert _do_check() == 0


def test_perf_artifact_disclaims_guarantees():
    text = (ROOT / "certification" / "PERF_SANITY.md").read_text(
        encoding="utf-8")
    assert "not guarantees" in text
    assert "makes no latency promises" in text
    assert "Machine:" in text  # numbers are tied to the measuring machine


def test_measurement_functions_run():
    results = measure()
    expected = {"registry load (97 skills, 94 drivers)",
                "mcp tool list build (210 tools)",
                "dispatch read action (mock, incl. audit)",
                "approval request+approve+consume",
                "audit log append",
                "idempotency reserve+commit+release",
                "credential resolution"}
    assert set(results) == expected
    for name, (median, mx) in results.items():
        assert median >= 0 and mx >= median, name
        # sanity, not an SLA: nothing may take longer than 30 s per op
        assert mx < 30_000, f"{name} pathologically slow: {mx} ms"

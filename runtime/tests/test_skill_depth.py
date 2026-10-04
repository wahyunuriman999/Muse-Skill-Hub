"""Depth markers for the README Skill List table are data-driven.

The Depth column must always match what the registry computes; this guards
the expectation-management fix suggested by a community reviewer (ini.patria):
thin skills like canva's 2 read-only actions must be visibly marked Limited.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent
TOOLS = RUNTIME / "tools"
REPO = RUNTIME.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "skill_depth", TOOLS / "skill_depth.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_depth_tiers_are_valid_and_complete():
    mod = _load()
    depths = mod.compute_depths()
    assert len(depths) == 97, f"expected 97 skills, got {len(depths)}"
    assert set(depths.values()) <= {"Full", "Standard", "Limited", "Stub"}
    assert depths["muse-early-access"] == "Stub"
    assert depths["canva"] == "Limited"  # the reviewer's example: 2 read-only actions


def test_check_passes_on_real_readme(monkeypatch):
    mod = _load()
    monkeypatch.setattr(sys, "argv", ["skill_depth.py", "--check"])
    assert mod.main() == 0


def test_check_detects_drift(tmp_path, monkeypatch):
    mod = _load()
    fake = tmp_path / "README.md"
    shutil.copy(REPO / "README.md", fake)
    text = fake.read_text(encoding="utf-8")
    # corrupt one depth cell: canva Limited -> Full
    corrupted = re_sub_canva(text)
    assert corrupted != text, "expected to corrupt exactly one canva row"
    fake.write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(mod, "README", fake)
    monkeypatch.setattr(sys, "argv", ["skill_depth.py", "--check"])
    assert mod.main() == 1


def re_sub_canva(text: str) -> str:
    import re
    return re.sub(
        r"(\| `canva` \| canva \| .*? \| )Limited( \|)",
        r"\1Full\2",
        text,
        count=1,
    )


def test_write_is_idempotent(tmp_path, monkeypatch):
    mod = _load()
    fake = tmp_path / "README.md"
    shutil.copy(REPO / "README.md", fake)
    monkeypatch.setattr(mod, "README", fake)
    monkeypatch.setattr(sys, "argv", ["skill_depth.py", "--write"])
    assert mod.main() == 0
    first = fake.read_text(encoding="utf-8")
    assert mod.main() == 0
    assert fake.read_text(encoding="utf-8") == first
    monkeypatch.setattr(sys, "argv", ["skill_depth.py", "--check"])
    assert mod.main() == 0

"""GATE 12 — clean installation.

The catalog must ship INSIDE the wheel so a clean install works outside
the source checkout. Proven here:
  1. SKILLS_DIR lives under the installed ``skillhub`` package
     (``skillhub/catalog``), not at the repo root;
  2. every catalog entry has the files the wheel must contain;
  3. the package-data globs in pyproject.toml actually match those files
     (so the built wheel cannot silently drop the catalog).
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from skillhub import registry
from skillhub.registry import SKILLS_DIR, load_registry

RUNTIME = Path(__file__).resolve().parent.parent


def _package_data_patterns() -> list[str]:
    """Read the skillhub package-data globs without tomllib (3.10-safe)."""
    text = (RUNTIME / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(
        r"\[tool\.setuptools\.package-data\]\s*\nskillhub\s*=\s*\[(.*?)\]",
        text, re.S)
    assert m, "no skillhub package-data in pyproject.toml"
    return re.findall(r'"([^"]+)"', m.group(1))


def test_catalog_lives_inside_package():
    pkg = Path(registry.__file__).resolve().parent
    assert SKILLS_DIR.resolve().is_relative_to(pkg), \
        f"SKILLS_DIR {SKILLS_DIR} is outside the installed package {pkg}"
    assert (SKILLS_DIR / "github" / "SKILL.md").exists()


def test_every_entry_has_packaged_files():
    reg = load_registry()
    assert len(reg) == 97
    missing = [n for n in reg
               if not (SKILLS_DIR / n / "SKILL.md").exists()
               or not (SKILLS_DIR / n / "manifest.yaml").exists()]
    assert missing == []


def test_package_data_covers_catalog():
    patterns = _package_data_patterns()
    assert patterns, "no package-data declared for skillhub"
    catalog_files = [p.relative_to(RUNTIME / "skillhub").as_posix()
                     for p in SKILLS_DIR.rglob("*")
                     if p.is_file() and p.suffix in {".md", ".yaml"}]
    assert catalog_files, "no catalog files found"
    uncovered = [f for f in catalog_files
                 if not any(fnmatch.fnmatch(f, pat) for pat in patterns)]
    assert uncovered == [], f"package-data misses: {uncovered[:5]}"

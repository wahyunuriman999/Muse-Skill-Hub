"""GATE 11 — generated documentation.

Generated artifacts (README metrics blocks, manifest.yaml files) must be
reproducible from ground truth and never hand-edited. Proven here:
  1. ``sync_readme.py --check`` is READ-ONLY: it reports drift without
     dirtying the working tree (previously it wrote first, then reported);
  2. ``--check`` fails when a metrics number is hand-edited;
  3. syncing is idempotent: a second run is a no-op;
  4. manifest generation is byte-deterministic across runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent
TOOLS = RUNTIME / "tools"


def _stale_readme(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    p.write_text(
        "# T\n\n<!-- METRICS:START -->\n"
        "**Version 0.0.0** · **1 skills**\n"
        "<!-- METRICS:END -->\n",
        encoding="utf-8")
    return p


def test_check_mode_is_read_only(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sync_readme", TOOLS / "sync_readme.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = _stale_readme(tmp_path, "README.md")
    runtime = _stale_readme(tmp_path, "RUNTIME.md")
    monkeypatch.setattr(mod, "README_ROOT", root)
    monkeypatch.setattr(mod, "README_RUNTIME", runtime)
    before = (root.read_text(), runtime.read_text())

    monkeypatch.setattr(sys, "argv", ["sync_readme.py", "--check"])
    rc = mod.main()
    assert rc == 1  # drift detected...
    # ...but nothing was written
    assert (root.read_text(), runtime.read_text()) == before


def test_check_mode_passes_when_in_sync(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sync_readme", TOOLS / "sync_readme.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = _stale_readme(tmp_path, "README.md")
    runtime = _stale_readme(tmp_path, "RUNTIME.md")
    monkeypatch.setattr(mod, "README_ROOT", root)
    monkeypatch.setattr(mod, "README_RUNTIME", runtime)

    monkeypatch.setattr(sys, "argv", ["sync_readme.py"])
    assert mod.main() == 0  # writes the fix
    monkeypatch.setattr(sys, "argv", ["sync_readme.py", "--check"])
    assert mod.main() == 0  # now clean
    # idempotent: syncing twice changes nothing the second time
    monkeypatch.setattr(sys, "argv", ["sync_readme.py"])
    assert mod.main() == 0
    snapshot = (root.read_text(), runtime.read_text())
    assert mod.main() == 0
    assert (root.read_text(), runtime.read_text()) == snapshot


def test_hand_edited_number_detected(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sync_readme", TOOLS / "sync_readme.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = _stale_readme(tmp_path, "README.md")
    runtime = _stale_readme(tmp_path, "RUNTIME.md")
    monkeypatch.setattr(mod, "README_ROOT", root)
    monkeypatch.setattr(mod, "README_RUNTIME", runtime)
    monkeypatch.setattr(sys, "argv", ["sync_readme.py"])
    assert mod.main() == 0
    # hand-edit a published number
    text = root.read_text(encoding="utf-8")
    root.write_text(text.replace("skills", "SKILLS"), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sync_readme.py", "--check"])
    assert mod.main() == 1


def test_manifest_generation_is_deterministic(tmp_path):
    from skillhub.manifests import manifest_for
    from skillhub.registry import load_registry
    reg = load_registry(apply_manifest_risks=False)
    first = {n: manifest_for(n, e) for n, e in reg.items()}
    reg2 = load_registry(apply_manifest_risks=False)
    second = {n: manifest_for(n, e) for n, e in reg2.items()}
    assert first == second
    # and the shipped files match the deterministic output
    from skillhub.registry import SKILLS_DIR
    for name, text in first.items():
        shipped = (SKILLS_DIR / name / "manifest.yaml").read_text(
            encoding="utf-8")
        assert shipped == text, f"{name}: shipped manifest not deterministic"

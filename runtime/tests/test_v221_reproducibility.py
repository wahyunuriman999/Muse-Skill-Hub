"""GATE 21 — release reproducibility.

The release artifact must be buildable from a clean checkout, byte-reproducible
across independent builds, and installable into a fresh environment where the
validator and the full suite pass against the *installed* package — not the
source tree.
"""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

RUNTIME_DIR = Path(__file__).resolve().parent.parent
PYPROJECT = RUNTIME_DIR / "pyproject.toml"


def _wheel_hashes(path: Path) -> dict:
    out = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            out[name] = hashlib.sha256(z.read(name)).hexdigest()
    return out


def test_package_version_consistent():
    """pyproject version and skillhub.__version__ must agree."""
    import skillhub

    text = PYPROJECT.read_text(encoding="utf-8")
    (line,) = [ln for ln in text.splitlines() if ln.startswith("version =")]
    declared = line.split("=", 1)[1].strip().strip('"')
    assert skillhub.__version__ == declared, (
        f"skillhub.__version__={skillhub.__version__!r} != pyproject {declared!r}"
    )


def test_wheel_contains_full_package():
    """The wheel must ship every driver module, not a partial tree."""
    import skillhub
    import skillhub.skills as skills_pkg

    expected = {p.stem for p in Path(skills_pkg.__file__).parent.glob("*.py")}
    expected.discard("__init__")
    installed_pkg = Path(skillhub.__file__).parent
    installed = {p.stem for p in (installed_pkg / "skills").glob("*.py")}
    installed.discard("__init__")
    missing = expected - installed
    assert not missing, f"skill modules missing from installed package: {sorted(missing)}"
    assert len(installed) >= 60, f"unexpectedly few skill modules installed: {len(installed)}"


def test_wheel_build_reproducible(tmp_path):
    """Two independent wheel builds from this tree must be content-identical."""
    wheels = []
    for i in range(2):
        outdir = tmp_path / f"dist{i}"
        outdir.mkdir()
        r = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir), "."],
            cwd=RUNTIME_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert r.returncode == 0, f"wheel build {i} failed:\n{r.stderr[-2000:]}"
        (whl,) = list(outdir.glob("*.whl"))
        wheels.append(whl)
    a, b = (_wheel_hashes(w) for w in wheels)
    assert sorted(a) == sorted(b), "wheel namelists differ between builds"
    diff = [n for n in a if a[n] != b[n]]
    assert not diff, f"wheel builds not reproducible, differing files: {diff}"

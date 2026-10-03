"""GATE 26 — PyPI/MCP packaging, beyond the existing coverage.

test_v221_clean_install.py already proves the catalog ships inside the
package, and test_v221_reproducibility.py already proves version
agreement and wheel byte-reproducibility. What neither covers:

  1. the pyproject version is pinned to the exact v2.3.0 gate value;
  2. a real ``python -m build`` produces BOTH wheel and sdist;
  3. ``twine check`` passes on both artifacts;
  4. the LICENSE file is present INSIDE both archives;
  5. visibility/server.json is valid JSON carrying the required MCP
     registry fields (name, version, pypi package identifier).

``build``/``twine`` are optional: missing tools skip with a named reason.
"""
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent
REPO = RUNTIME.parent
EXPECTED_VERSION = "2.3.0"
LICENSE_BASENAMES = {"LICENSE", "LICENSE.TXT", "LICENSE.MD"}


def _pyproject_version() -> str:
    """Read the version without tomllib (3.10-safe)."""
    text = (RUNTIME / "pyproject.toml").read_text(encoding="utf-8")
    (line,) = [ln for ln in text.splitlines()
               if ln.strip().startswith("version =")]
    return line.split("=", 1)[1].strip().strip('"')


def _pyproject_name() -> str:
    text = (RUNTIME / "pyproject.toml").read_text(encoding="utf-8")
    (line,) = [ln for ln in text.splitlines()
               if ln.strip().startswith("name =")]
    return line.split("=", 1)[1].strip().strip('"')


@pytest.fixture(scope="module")
def dist_artifacts(tmp_path_factory):
    """One real ``python -m build`` (wheel + sdist) shared by the tests."""
    pytest.importorskip("build")
    outdir = tmp_path_factory.mktemp("dist")
    r = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(outdir), "."],
        cwd=RUNTIME, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"python -m build failed:\n{r.stderr[-2000:]}"
    wheels = list(outdir.glob("*.whl"))
    sdists = list(outdir.glob("*.tar.gz"))
    return {"wheel": wheels, "sdist": sdists, "log": r.stderr}


def test_pyproject_version_is_230_dev0():
    """The v2.3.0 gate pins the exact pre-release version string."""
    assert _pyproject_version() == EXPECTED_VERSION, (
        f"pyproject version {_pyproject_version()!r} != {EXPECTED_VERSION!r}")


def test_build_produces_wheel_and_sdist(dist_artifacts):
    """A full build yields both artifacts, named with the gate version."""
    assert len(dist_artifacts["wheel"]) == 1, dist_artifacts["wheel"]
    assert len(dist_artifacts["sdist"]) == 1, dist_artifacts["sdist"]
    for artifact in dist_artifacts["wheel"] + dist_artifacts["sdist"]:
        assert EXPECTED_VERSION in artifact.name, artifact.name


def test_twine_check_passes(dist_artifacts):
    """Both artifacts pass twine check (what PyPI will validate)."""
    pytest.importorskip("twine")
    artifacts = [str(p) for p in
                 dist_artifacts["wheel"] + dist_artifacts["sdist"]]
    r = subprocess.run(
        [sys.executable, "-m", "twine", "check", *artifacts],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"twine check failed:\n{r.stdout}\n{r.stderr}"


def _license_members(names: list[str]) -> list[str]:
    return [n for n in names
            if Path(n).name.upper() in LICENSE_BASENAMES]


def test_license_inside_wheel_and_sdist(dist_artifacts):
    """The LICENSE file must be present INSIDE both archives."""
    (wheel,) = dist_artifacts["wheel"]
    (sdist,) = dist_artifacts["sdist"]
    with zipfile.ZipFile(wheel) as z:
        wheel_lic = _license_members(z.namelist())
    with tarfile.open(sdist) as t:
        sdist_lic = _license_members(t.getnames())
    assert wheel_lic, f"no LICENSE inside wheel {wheel.name}"
    assert sdist_lic, f"no LICENSE inside sdist {sdist.name}"


def test_server_json_is_valid_mcp_registry_metadata():
    """visibility/server.json parses and carries the required MCP fields."""
    path = REPO / "visibility" / "server.json"
    assert path.exists(), "visibility/server.json missing"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("name"), "server.json: missing/empty 'name'"
    assert data.get("version"), "server.json: missing/empty 'version'"
    packages = data.get("packages") or []
    assert packages, "server.json: missing/empty 'packages'"
    assert packages[0].get("registryType") == "pypi"
    assert packages[0].get("identifier") == _pyproject_name(), (
        f"server.json package identifier {packages[0].get('identifier')!r} "
        f"!= pyproject name {_pyproject_name()!r}")

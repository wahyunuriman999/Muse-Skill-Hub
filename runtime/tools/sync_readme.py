"""Sync README metrics from authoritative metadata (v2.2+).

Hardcoded numbers in READMEs go stale (v2.1.0 shipped a README claiming
both "67 passing tests" and "91 passing tests"). This tool regenerates
the metrics blocks from ground truth:

- version / skills / implemented drivers / stubs / MCP tools
  → ``python -m skillhub.cli metadata`` (the registry itself)
- passing tests → ``pytest --collect-only`` (the test suite itself)

Marked regions are replaced in place::

    <!-- METRICS:START --> ... <!-- METRICS:END -->

Usage:  python tools/sync_readme.py [--check]

``--check`` exits non-zero when a README is out of sync (for CI).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
RUNTIME = ROOT / "runtime"
README_ROOT = ROOT / "README.md"
README_RUNTIME = RUNTIME / "README.md"


def collect_metadata() -> dict:
    out = subprocess.run(
        [sys.executable, "-m", "skillhub.cli", "metadata"],
        cwd=RUNTIME, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def count_tests() -> int:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=RUNTIME, capture_output=True, text=True)
    # last non-empty line looks like "91 tests collected in 2.34s"
    # (or "1 test collected" / "N errors" on failure)
    for line in reversed(out.stdout.strip().splitlines()):
        line = line.strip()
        m = re.match(r"(\d+) tests? collected", line)
        if m:
            return int(m.group(1))
    raise RuntimeError("could not parse pytest --collect-only output:\n"
                       + out.stdout[-2000:] + "\n" + out.stderr[-2000:])


def metrics_block(meta: dict, n_tests: int, runtime_readme: bool = False) -> str:
    v = meta["catalog_version"]
    lines = [
        "<!-- METRICS:START -->",
        f"_Generated from registry + test suite — do not hand-edit. "
        f"Run `python tools/sync_readme.py`._",
        "",
        f"**Version {v}** · **{meta['skills']} skills** · "
        f"**{meta['implemented']} executable drivers** "
        f"({meta['stubs']} honest stubs) · "
        f"**{meta['mcp_tools']} MCP tools** · "
        f"**{n_tests} passing tests**",
        "<!-- METRICS:END -->",
    ]
    return "\n".join(lines)


def _replace_block(text: str, block: str) -> str:
    pattern = re.compile(r"<!-- METRICS:START -->.*?<!-- METRICS:END -->",
                         re.S)
    if not pattern.search(text):
        raise RuntimeError("no <!-- METRICS:... --> block found")
    return pattern.sub(lambda _: block, text, count=1)


def sync(path: Path, meta: dict, n_tests: int) -> bool:
    """Rewrite the metrics block. Returns True when the file changed."""
    text = path.read_text(encoding="utf-8")
    new = _replace_block(text, metrics_block(meta, n_tests))
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    check = "--check" in sys.argv
    meta = collect_metadata()
    n_tests = count_tests()
    print(f"metadata: {meta} | tests: {n_tests}")
    changed = []
    for path in (README_ROOT, README_RUNTIME):
        # ensure the marker block exists before syncing
        if "<!-- METRICS:START -->" not in path.read_text(encoding="utf-8"):
            print(f"SKIP {path}: no METRICS block (add markers first)")
            continue
        if sync(path, meta, n_tests):
            changed.append(str(path))
    if check and changed:
        print("OUT OF SYNC:", ", ".join(changed))
        return 1
    for c in changed:
        print("updated", c)
    if not changed:
        print("already in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())

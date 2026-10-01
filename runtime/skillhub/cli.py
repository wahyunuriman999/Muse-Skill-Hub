"""skillhub CLI: validate | metadata

    python -m skillhub.cli validate   # Skill Conformance Test v1
    python -m skillhub.cli metadata    # machine-readable catalog counts
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import __version__
from .driver import RISK_LEVELS
from .policy import risk_for
from .registry import SKILLS_DIR, load_registry

_VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
_SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[bap]-"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]


def _load_manifest(name: str) -> dict | None:
    # minimal YAML reader for our generated manifests (flat + one list level)
    path = SKILLS_DIR / name / "manifest.yaml"
    if not path.exists():
        return None
    data: dict = {}
    actions: list[dict] = []
    current: dict | None = None
    in_actions = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("  - name: "):
            current = {"name": raw.split("  - name: ", 1)[1].strip()}
            actions.append(current)
            in_actions = True
        elif raw.startswith("actions:"):
            in_actions = True
        elif raw.startswith("auth:") or raw.startswith("dependencies:"):
            in_actions = False
            current = None
        elif in_actions and current is not None and raw.startswith("    "):
            k, _, v = raw.strip().partition(":")
            current[k.strip()] = v.strip()
        elif not in_actions and ":" in raw and not raw.startswith(" "):
            k, _, v = raw.partition(":")
            data[k.strip()] = v.strip().strip('"')
    data["actions"] = actions
    return data


def validate() -> int:
    reg = load_registry()
    failures: list[str] = []
    warnings: list[str] = []
    names = list(reg)

    if len(set(names)) != len(names):
        failures.append("duplicate skill names")

    for name, entry in reg.items():
        tag = f"[{name}]"
        md = SKILLS_DIR / name / "SKILL.md"
        if not md.exists():
            failures.append(f"{tag} missing SKILL.md")
            continue
        text = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.S)
        front = m.group(1) if m else ""
        for field in ("name", "title", "description"):
            if f"{field}:" not in front:
                failures.append(f"{tag} frontmatter missing '{field}'")

        # action schema checks
        for aname, ad in entry.actions.items():
            for pname, spec in (ad.parameters or {}).items():
                t = spec.get("type") if isinstance(spec, dict) else None
                if t and t not in _VALID_TYPES:
                    failures.append(f"{tag} action '{aname}': unknown type '{t}' "
                                    f"for param '{pname}'")
            for req in ad.required or []:
                if req not in (ad.parameters or {}):
                    failures.append(f"{tag} action '{aname}': required '{req}' "
                                    "not declared in parameters")
            risk = risk_for(name, aname, ad.risk)
            if risk not in RISK_LEVELS:
                failures.append(f"{tag} action '{aname}': unknown risk '{risk}'")
            # doc drift: driver action should be mentioned in SKILL.md
            if aname not in text and aname.replace("_", " ") not in text.lower():
                warnings.append(f"{tag} action '{aname}' not mentioned in SKILL.md")

        # manifest drift
        manifest = _load_manifest(name)
        if manifest is None:
            warnings.append(f"{tag} missing manifest.yaml (run generate_manifests.py)")
        else:
            mactions = {a["name"] for a in manifest.get("actions", [])}
            dactions = set(entry.actions)
            if mactions != dactions:
                failures.append(
                    f"{tag} manifest/driver drift: manifest={sorted(mactions)} "
                    f"driver={sorted(dactions)}")

        # secret leakage scan
        mod = Path(__file__).resolve().parent / "skills" / \
            f"{name.replace('-', '_')}.py"
        if mod.exists():
            src = mod.read_text(encoding="utf-8")
            for pat in _SECRET_PATTERNS:
                if pat.search(src):
                    warnings.append(f"{tag} driver may contain a hardcoded secret")

    # doc counts consistency
    readme = Path(__file__).resolve().parent.parent.parent / "README.md"
    n_impl = sum(1 for e in reg.values() if e.implemented)
    if readme.exists():
        rtext = readme.read_text(encoding="utf-8")
        for label, value in (("skills", len(reg)), ("driver", n_impl)):
            if str(value) not in rtext:
                warnings.append(f"README does not mention current count {value} ({label})")

    print(f"skillhub validate v{__version__}: {len(reg)} skills scanned")
    for w in warnings:
        print(f"  WARN  {w}")
    for f in failures:
        print(f"  FAIL  {f}")
    if failures:
        print(f"RESULT: {len(failures)} FAILURES, {len(warnings)} warnings")
        return 1
    print(f"RESULT: PASS ({len(warnings)} warnings)")
    return 0


def metadata() -> int:
    from .registry import mcp_tools
    reg = load_registry()
    tools = mcp_tools(reg)
    print(json.dumps({
        "catalog_version": __version__,
        "skills": len(reg),
        "implemented": sum(1 for e in reg.values() if e.implemented),
        "stubs": sum(1 for e in reg.values() if not e.implemented),
        "mcp_tools": len(tools),
    }, indent=2))
    return 0


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        sys.exit(validate())
    if cmd == "metadata":
        sys.exit(metadata())
    print(f"unknown command: {cmd} (validate | metadata)")
    sys.exit(2)


if __name__ == "__main__":
    main()

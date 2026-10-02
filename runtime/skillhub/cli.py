"""skillhub CLI: validate | metadata | audit-verify | idempotency

    python -m skillhub.cli validate   # Skill Conformance Test v1
    python -m skillhub.cli metadata    # machine-readable catalog counts
    python -m skillhub.cli audit-verify           # verify audit hash chain
    python -m skillhub.cli idempotency list       # list idempotency keys
    python -m skillhub.cli idempotency release K  # operator escape hatch
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import __version__
from .driver import RISK_LEVELS
from .manifests import manifest_for
from .policy import risk_for
from .registry import SKILLS_DIR, load_registry

_VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}
_SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[bap]-"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]


def is_destructive_name(action_name: str) -> bool:
    """Heuristic: does the action NAME declare an irreversible side effect?

    The v2.2.0-agreed verb list. Deliberately conservative: bare-substring
    verbs like ``kill`` are excluded (``s``+``kill`` = "skill" would false-
    positive on every skill-related action). The check is a backstop, not a
    proof — the manifest risk is the canonical classifier; this catches a
    destructive action that was (accidentally or maliciously) left at the
    bare-confirm ``write`` tier.
    """
    lname = action_name.lower()
    hit = any(v in lname for v in (
        "delete", "destroy", "revoke", "terminate", "purge", "wipe"))
    return hit or lname.startswith("remove_") or lname.endswith("_delete")


def manifest_contract_drift(name: str, entry) -> list[str]:
    """Diff the shipped manifest.yaml against a fresh generator run.

    Returns failure lines (empty when in sync). The generator preserves
    hand-tuned manifest risks, so any remaining diff is real drift:
    params, required lists, output schemas, descriptions, versions, or
    action sets that changed in the driver/SKILL.md without regenerating.
    """
    path = SKILLS_DIR / name / "manifest.yaml"
    if not path.exists():
        return [f"missing manifest.yaml (run tools/generate_manifests.py)"]
    expected = manifest_for(name, entry)
    actual = path.read_text(encoding="utf-8")
    if actual == expected:
        return []
    import difflib
    diff = list(difflib.unified_diff(
        expected.splitlines(), actual.splitlines(),
        "generated", "shipped", lineterm="", n=1))
    excerpt = "\n    ".join(diff[:14])
    return [f"manifest.yaml drift from driver/SKILL.md "
            f"(run tools/generate_manifests.py):\n    {excerpt}"]


def validate() -> int:
    reg = load_registry()
    # Raw driver view (no manifest risk override): driver edits — including
    # risk bumps — must be visible to the generator, otherwise a stale
    # manifest would mask them.
    regen = load_registry(apply_manifest_risks=False)
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
            # JSON-Schema validity (Draft 2020-12): malformed schemas are a
            # conformance failure here, never a surprise at dispatch time
            try:
                from jsonschema import Draft202012Validator
                Draft202012Validator.check_schema({
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": ad.parameters or {},
                    "required": ad.required or [],
                })
                if ad.output_schema:
                    Draft202012Validator.check_schema(ad.output_schema)
            except Exception as exc:
                failures.append(f"{tag} action '{aname}': invalid JSON Schema: "
                                f"{exc}".split("\n")[0])
            risk = risk_for(name, aname, ad.risk)
            if risk not in RISK_LEVELS:
                failures.append(f"{tag} action '{aname}': unknown risk '{risk}'")
            # security conformance: an action whose name declares an
            # irreversible side effect must not be classifiable with a bare
            # confirm=true (risk 'write'). Destructive verbs require a risk
            # level that forces a real approval_id.
            if is_destructive_name(aname) and risk == "write":
                failures.append(
                    f"{tag} action '{aname}': destructive name but risk "
                    f"'write' (bare confirm=true suffices) — bump to "
                    f"'destructive' (or another approval-gated risk)")
            # doc drift: driver action MUST be mentioned in SKILL.md — the doc
            # is part of the contract, an undocumented action is a breach.
            if aname not in text and aname.replace("_", " ") not in text.lower():
                failures.append(f"{tag} action '{aname}' not mentioned in SKILL.md")

        # manifest contract: the shipped manifest.yaml must be EXACTLY what
        # the generator produces from driver + SKILL.md (modulo hand-tuned
        # risks, which the generator preserves). Any other drift — params,
        # required, output_schema, descriptions, versions, action sets —
        # means the contract lies. Regenerate with tools/generate_manifests.py.
        for _mline in manifest_contract_drift(name, regen[name]):
            failures.append(f"{tag} {_mline}")

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


def audit_verify() -> int:
    from .audit import verify_chain
    report = verify_chain()
    print(json.dumps(report, indent=2))
    if report["ok"]:
        print(f"RESULT: audit chain OK "
              f"({report['chained']} chained, {report['legacy']} legacy)")
        return 0
    print(f"RESULT: AUDIT CHAIN BROKEN at line "
          f"{report['first_bad']['line']}: {report['first_bad']['reason']}")
    return 1


def idempotency() -> int:
    """Operator tooling for idempotency keys.

    skillhub idempotency list              # show all key records
    skillhub idempotency release <key>      # delete one record (escape hatch
                                           # for keys stuck PENDING after a
                                           # crash — only after verifying no
                                           # execution is running for it)
    skillhub idempotency recover [--dry-run]  # classify stale PENDING keys
                                           # via the write-ahead log; safely
                                           # reclaims provable pre-call
                                           # crashes, reports the rest
    """
    from .registry import _idem_list, _idem_release, idempotency_recover
    args = sys.argv[2:]
    if not args or args[0] == "list":
        rows = _idem_list()
        slim = [{k: r.get(k) for k in ("idempotency_key", "skill", "action",
                                      "status", "error_code", "claimed_at")}
                for r in rows]
        print(json.dumps(slim, indent=2))
        print(f"{len(slim)} idempotency key(s)")
        return 0
    if args[0] == "release" and len(args) == 2:
        if _idem_release(args[1]):
            print(f"released idempotency key '{args[1]}' (audit-logged)")
            return 0
        print(f"no such idempotency key: '{args[1]}'")
        return 1
    if args[0] == "recover":
        dry = "--dry-run" in args[1:]
        report = idempotency_recover(apply=not dry)
        print(json.dumps(report, indent=2))
        if dry:
            print("dry run — nothing was changed")
        else:
            print(f"reclaimed: {len(report['reclaimed'])}, "
                  f"needs_reconciliation: "
                  f"{len(report['needs_reconciliation'])}, "
                  f"in_flight: {len(report['in_flight'])}, "
                  f"settled: {report['settled']}")
        return 0
    print("usage: skillhub idempotency [list | release <key> | recover [--dry-run]]")
    return 2


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        sys.exit(validate())
    if cmd == "metadata":
        sys.exit(metadata())
    if cmd == "audit-verify":
        sys.exit(audit_verify())
    if cmd == "idempotency":
        sys.exit(idempotency())
    print(f"unknown command: {cmd} "
          f"(validate | metadata | audit-verify | idempotency)")
    sys.exit(2)


if __name__ == "__main__":
    main()

"""Manifest generation: the single source of the shipped contract.

``manifest.yaml`` per skill is generated from the driver registry
(``manifest_for``). Risk preservation rule: the manifest is the canonical
risk source and may be hand-tuned — the generator only overwrites a
manifest risk when the driver declares an explicit ``ActionDef(risk=...)``;
otherwise the existing manifest risk is kept (new actions fall back to the
driver default).

``skillhub validate`` regenerates every manifest in memory and fails on
ANY drift, so driver / manifest / SKILL.md can never silently disagree.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub.policy import risk_for
from skillhub.registry import SKILLS_DIR, load_registry


def _yaml_str(value) -> str:
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, list):
        if not value:
            return "[]"
        return "[" + ", ".join(_yaml_str(v) for v in value) + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = ", ".join(f"{k}: {_yaml_str(v)}" for k, v in value.items())
        return "{" + items + "}"
    return _yaml_str(str(value))


def manifest_for(name, entry) -> str:
    from skillhub.registry import _frontmatter, _manifest_risks
    meta, _ = _frontmatter(SKILLS_DIR / name / "SKILL.md")
    # The manifest is the canonical risk source and may be hand-tuned
    # (e.g. gmail.send_message → communication). Never clobber a tuned
    # risk with a driver's non-explicit default: only an explicit
    # ActionDef(risk=...) overrides what's already in the manifest.
    existing_risks = _manifest_risks(name)
    lines = [
        'schema_version: "1"',
        f"name: {name}",
        f"version: {_yaml_str(entry.version)}",
        f"title: {_yaml_str(meta.get('title', name))}",
        f"description: {_yaml_str(entry.description)}",
        "kind: skill",
        "lifecycle: stable",
        "actions:",
    ]
    for aname, ad in sorted(entry.actions.items()):
        if ad.risk_explicit:
            risk = risk_for(name, aname, ad.risk)
        else:
            # preserve the hand-tuned manifest risk; fall back to the
            # driver's default only for brand-new actions
            risk = existing_risks.get(aname) or risk_for(name, aname, ad.risk)
        approval = "required" if risk != "read" else "not_required"
        lines += [
            f"  - name: {aname}",
            f"    type: {'write' if risk != 'read' else 'read'}",
            f"    risk: {risk}",
            f"    approval: {approval}",
            f"    supports_idempotency_key: {_yaml_str(ad.supports_idempotency_key)}",
            f"    required_scopes: {_yaml_str(ad.required_scopes or [])}",
            "    input_schema:",
            "      type: object",
            f"      properties: {_yaml_str(ad.parameters or {})}",
            f"      required: {_yaml_str(ad.required or [])}",
            f"    output_schema: {_yaml_str(ad.output_schema or {})}",
        ]
    lines += [
        "auth:",
        f"  required_env: {_yaml_str(entry.required_env)}",
        "dependencies: []",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    # Bypass the manifest-risk override: manifests are GENERATED from the
    # drivers, so driver edits (e.g. a risk bump) must propagate.
    reg = load_registry(apply_manifest_risks=False)
    n = 0
    for name, entry in reg.items():
        path = SKILLS_DIR / name / "manifest.yaml"
        path.write_text(manifest_for(name, entry), encoding="utf-8")
        n += 1
    print(f"wrote {n} manifests")


if __name__ == "__main__":
    main()

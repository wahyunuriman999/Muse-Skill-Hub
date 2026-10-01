"""GATE 9 — manifest / driver / SKILL.md contract.

The shipped ``manifest.yaml`` must be EXACTLY what the generator produces
from driver + SKILL.md (modulo hand-tuned risks, which the generator
preserves). ``skillhub validate`` regenerates every manifest in memory and
FAILS on any drift — params, required lists, output schemas, descriptions,
versions, action sets. A driver action undocumented in SKILL.md is also a
failure: the doc is part of the contract.
"""
from __future__ import annotations

import pytest

from skillhub import registry
from skillhub.cli import manifest_contract_drift, validate
from skillhub.driver import ActionDef
from skillhub.manifests import manifest_for


# --- the real tree: zero drift across all 97 skills -----------------------------

def test_all_shipped_manifests_match_generator():
    regen = registry.load_registry(apply_manifest_risks=False)
    drifted = []
    for name, entry in regen.items():
        problems = manifest_contract_drift(name, entry)
        if problems:
            drifted.append((name, problems))
    assert drifted == []


def test_validator_passes_on_clean_tree():
    assert validate() == 0


# --- drift is caught ------------------------------------------------------------

def _setup_skill(tmp_path, monkeypatch):
    """Patch SKILLS_DIR everywhere and write the SKILL.md.

    Must run BEFORE manifest_for(): the generator reads SKILL.md and the
    existing manifest from disk through the patched directory.
    """
    from skillhub import cli
    import skillhub.manifests as manifests
    import skillhub.registry as regmod
    # SKILLS_DIR is bound as a module global in three namespaces
    for mod in (cli, manifests, regmod):
        monkeypatch.setattr(mod, "SKILLS_DIR", tmp_path)
    skill_dir = tmp_path / "contractskill"
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: contractskill\ntitle: Contract\ndescription: x\n---\n\n"
        "do_thing does a thing.\n",
        encoding="utf-8")
    return skill_dir


def _write_manifest(skill_dir, entry):
    (skill_dir / "manifest.yaml").write_text(
        manifest_for("contractskill", entry), encoding="utf-8")


def _entry(**action_kwargs):
    async def h(params):
        return {"ok": True}
    ad = ActionDef("does a thing",
                   {"x": {"type": "string"}}, ["x"], h, write=True,
                   **action_kwargs)
    return registry.SkillEntry(name="contractskill", description="x",
                               implemented=True, version="1.0.0",
                               actions={"do_thing": ad})


def test_param_drift_fails(tmp_path, monkeypatch):
    skill_dir = _setup_skill(tmp_path, monkeypatch)
    entry = _entry()
    _write_manifest(skill_dir, entry)
    assert manifest_contract_drift("contractskill", entry) == []

    # driver gains a parameter, manifest not regenerated → drift
    entry.actions["do_thing"].parameters["y"] = {"type": "integer"}
    problems = manifest_contract_drift("contractskill", entry)
    assert problems and "drift" in problems[0]


def test_required_list_drift_fails(tmp_path, monkeypatch):
    skill_dir = _setup_skill(tmp_path, monkeypatch)
    entry = _entry()
    _write_manifest(skill_dir, entry)
    entry.actions["do_thing"].required = []
    problems = manifest_contract_drift("contractskill", entry)
    assert problems and "drift" in problems[0]


def test_output_schema_drift_fails(tmp_path, monkeypatch):
    skill_dir = _setup_skill(tmp_path, monkeypatch)
    entry = _entry()
    _write_manifest(skill_dir, entry)
    entry.actions["do_thing"].output_schema = {
        "type": "object", "properties": {"ok": {"type": "boolean"}}}
    problems = manifest_contract_drift("contractskill", entry)
    assert problems and "drift" in problems[0]


def test_missing_manifest_fails(tmp_path, monkeypatch):
    _setup_skill(tmp_path, monkeypatch)
    problems = manifest_contract_drift("contractskill", _entry())
    assert problems and "missing manifest.yaml" in problems[0]


def test_hand_tuned_risk_is_not_drift(tmp_path, monkeypatch):
    # the generator preserves a hand-tuned manifest risk: tuning the risk
    # must NOT count as drift.
    skill_dir = _setup_skill(tmp_path, monkeypatch)
    entry = _entry()
    _write_manifest(skill_dir, entry)
    manifest_path = skill_dir / "manifest.yaml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            "    risk: write", "    risk: destructive", 1),
        encoding="utf-8")
    assert manifest_contract_drift("contractskill", entry) == []


def test_undocumented_action_fails_validate(tmp_path, monkeypatch):
    from skillhub import cli
    skill_dir = _setup_skill(tmp_path, monkeypatch)
    entry = _entry()
    # SKILL.md mentions do_thing; add an action it does not mention
    async def h2(params):
        return {"ok": True}
    entry.actions["secret_action"] = ActionDef(
        "hidden", {}, [], h2, write=True)
    _write_manifest(skill_dir, entry)  # manifest in sync; only the doc is off
    monkeypatch.setattr(cli, "load_registry",
                        lambda **kw: {"contractskill": entry})
    assert validate() == 1

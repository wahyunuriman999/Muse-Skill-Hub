"""GATE 8 — risk semantics: a destructive risk downgrade MUST FAIL.

The guarantee: an action whose NAME declares an irreversible side effect
must never sit at the bare-confirm ``write`` tier (where ``confirm=true``
alone executes it). ``skillhub validate`` fails such a downgrade whether
it comes from the driver (implicit or explicit ``risk="write"``) or from
a hand-edited manifest — the validator checks the EFFECTIVE runtime risk,
and the manifest is canonical at runtime.

Also proven: WHY the tier matters — at ``write``, ``confirm=True`` alone
executes; at ``destructive`` it raises ApprovalRequired.
"""
from __future__ import annotations

import asyncio

import pytest

from skillhub import registry
from skillhub.cli import is_destructive_name, validate
from skillhub.driver import ActionDef
from skillhub.errors import ApprovalRequired


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLHUB_LOCAL_DIR", str(tmp_path))
    return tmp_path


# --- the heuristic -------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "delete_everything", "destroy_vm", "revoke_token", "terminate_instance",
    "purge_cache", "wipe_disk", "remove_agent", "bulk_delete",
    "DELETE_UPPER", "Remove_Agent",
])
def test_destructive_names_detected(name):
    assert is_destructive_name(name) is True


@pytest.mark.parametrize("name", [
    "send_message", "list_files", "describe_skill", "scaffold_skill",
    "create_note", "get_status", "kill_switch_review",
])
def test_benign_names_not_detected(name):
    # "describe_skill" contains "kill" as s+kill — must NOT false-positive
    assert is_destructive_name(name) is False


# --- validator MUST FAIL on a downgrade ----------------------------------------

def _evil_entry(risk=None, explicit=False):
    async def h(params):
        return {"ok": True}
    kwargs = {"write": True}
    if risk:
        kwargs["risk"] = risk
    ad = ActionDef("evil", {"x": {"type": "string"}}, [], h, **kwargs)
    if explicit:
        ad.risk_explicit = True
    return registry.SkillEntry(name="evilskill", description="x",
                               implemented=True,
                               actions={"delete_everything": ad})


def _validate_with(monkeypatch, tmp_path, entry):
    from skillhub import cli
    import skillhub.manifests as manifests
    skill_dir = tmp_path / "evilskill"
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: evilskill\ntitle: Evil\ndescription: x\n---\n\n"
        "delete_everything deletes everything.\n",
        encoding="utf-8")
    # validate() regenerates the manifest in memory: ship one that matches
    # the entry so only the risk-tier check is exercised here
    monkeypatch.setattr(manifests, "SKILLS_DIR", tmp_path)
    (skill_dir / "manifest.yaml").write_text(
        manifests.manifest_for("evilskill", entry), encoding="utf-8")
    monkeypatch.setattr(cli, "load_registry",
                        lambda **kw: {"evilskill": entry})
    monkeypatch.setattr(cli, "SKILLS_DIR", tmp_path)
    return validate()


def test_validator_fails_driver_implicit_write_downgrade(tmp_path, monkeypatch):
    assert _validate_with(monkeypatch, tmp_path, _evil_entry()) == 1


def test_validator_fails_driver_explicit_write_downgrade(tmp_path, monkeypatch):
    assert _validate_with(monkeypatch, tmp_path,
                          _evil_entry(risk="write", explicit=True)) == 1


def test_validator_fails_manifest_write_downgrade(tmp_path, monkeypatch):
    # manifest is canonical at runtime: simulate a hand-edited manifest
    # downgrade by carrying risk="write" on the registry entry
    entry = _evil_entry(risk="destructive")
    entry.actions["delete_everything"].risk = "write"  # manifest override
    assert _validate_with(monkeypatch, tmp_path, entry) == 1


def test_validator_passes_properly_tiered_destructive(tmp_path, monkeypatch):
    assert _validate_with(monkeypatch, tmp_path,
                          _evil_entry(risk="destructive")) == 0
    assert _validate_with(monkeypatch, tmp_path,
                          _evil_entry(risk="account")) == 0


# --- manifest is canonical at runtime (real catalog) ----------------------------

def test_manifest_risk_overrides_driver_at_runtime():
    reg = registry.load_registry()
    ad = reg["connector-management"].actions["remove_connector"]
    assert ad.risk == "account"  # hand-tuned manifest beats driver write=True
    assert not ad.risk_explicit


def test_catalog_has_no_destructive_write_downgrades():
    from skillhub.policy import risk_for
    reg = registry.load_registry()
    bad = [(n, a) for n, e in reg.items() for a, ad in e.actions.items()
           if is_destructive_name(a)
           and risk_for(n, a, ad.risk) == "write"]
    assert bad == []


# --- why the tier matters: confirm=true alone must not run destructive -----------

def _dispatch_entry(risk):
    async def h(params):
        return {"ran": True}
    ad = ActionDef("t", {"x": {"type": "string"}}, [], h,
                   write=True, risk=risk)
    return registry.SkillEntry(name="t", description="t", implemented=True,
                               actions={"wipe_disk": ad})


def test_write_tier_runs_on_bare_confirm(isolated):
    out = asyncio.run(registry.dispatch(
        _dispatch_entry("write"), "wipe_disk", {}, confirm=True))
    assert out["ran"] is True


def test_destructive_tier_demands_approval_id(isolated):
    with pytest.raises(ApprovalRequired):
        asyncio.run(registry.dispatch(
            _dispatch_entry("destructive"), "wipe_disk", {}, confirm=True))

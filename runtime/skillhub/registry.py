"""Skill registry: turns the skills/*/SKILL.md catalog into executable MCP tools.

Every skill directory with a SKILL.md becomes one MCP tool. Skills with a
driver module in skillhub.skills get real executable actions; the rest are
registered honestly as catalog-only (driver_not_implemented) so the tool
surface is complete and LLM clients can discover all 97 skills.
"""
from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .driver import ActionDef
from .errors import ConfirmationRequired, DriverNotImplemented, SkillError

# skill name -> python module name when they differ
MODULE_OVERRIDES = {
    "places-search": "places_search",
    # "threads" and "meta-threads" are the same Threads account skill;
    # both names share the real driver.
    "threads": "meta_threads",
}

CATALOG_DIR = Path(__file__).resolve().parent.parent.parent / "skills"


def _parse_frontmatter(path: Path) -> dict:
    """Minimal YAML-frontmatter parser (our files use simple `key: value`)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    data: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        data[key] = value
    return data


@dataclass
class SkillEntry:
    name: str
    title: str
    description: str
    implemented: bool
    actions: dict[str, ActionDef] = field(default_factory=dict)
    required_env: list[str] = field(default_factory=list)
    setup_help: str = ""


def _load_driver(name: str):
    module_name = MODULE_OVERRIDES.get(name, name.replace("-", "_"))
    try:
        return importlib.import_module(f"skillhub.skills.{module_name}")
    except ImportError:
        return None


def load_registry(catalog_dir: Path | None = None) -> dict[str, SkillEntry]:
    catalog = Path(catalog_dir) if catalog_dir else CATALOG_DIR
    registry: dict[str, SkillEntry] = {}
    for skill_dir in sorted(catalog.iterdir()):
        fm_path = skill_dir / "SKILL.md"
        if not skill_dir.is_dir() or not fm_path.exists():
            continue
        fm = _parse_frontmatter(fm_path)
        name = fm.get("name") or skill_dir.name
        title = fm.get("title") or name.replace("-", " ").title()
        description = fm.get("description") or f"Capability: {title}."
        driver = _load_driver(name)
        if driver is not None:
            registry[name] = SkillEntry(
                name=name,
                title=title,
                description=description,
                implemented=True,
                actions=getattr(driver, "ACTIONS", {}),
                required_env=getattr(driver, "REQUIRED_ENV", []),
                setup_help=getattr(driver, "SETUP_HELP", ""),
            )
        else:
            registry[name] = SkillEntry(
                name=name, title=title, description=description, implemented=False
            )
    return registry


def _missing_env(entry: SkillEntry) -> list[str]:
    return [v for v in entry.required_env if not os.environ.get(v)]


async def dispatch(entry: SkillEntry, action: str, params: dict, confirm: bool) -> dict:
    """Execute one skill action with read/write isolation enforced."""
    if not entry.implemented or action not in entry.actions:
        raise DriverNotImplemented(entry.name)
    action_def = entry.actions[action]
    if action_def.write and not confirm:
        preview = {k: params.get(k) for k in action_def.required}
        raise ConfirmationRequired(entry.name, action, preview)
    missing = _missing_env(entry)
    if missing:
        from .errors import CredentialsMissing

        raise CredentialsMissing(entry.name, missing, entry.setup_help)
    try:
        result = await action_def.handler(params or {})
    except SkillError:
        raise
    except Exception as exc:  # never leak tracebacks to the LLM as success
        from .errors import UpstreamError

        raise UpstreamError(entry.name, f"{type(exc).__name__}: {exc}") from exc
    if isinstance(result, dict):
        return result
    return {"status": "ok", "result": result}


def tool_schema(entry: SkillEntry) -> dict:
    """Build the MCP input schema for one skill tool."""
    if entry.implemented:
        actions = entry.actions
        action_descriptions = "\n".join(
            f"- {an}: {ad.description}"
            + (" [WRITE: needs confirm=true]" if ad.write else "")
            for an, ad in actions.items()
        )
        description = (
            f"{entry.description}\n\nActions:\n{action_descriptions}\n\n"
            f"Pass action + params. Write actions require confirm=true."
        )
        if entry.required_env:
            description += f"\nNeeds env: {', '.join(entry.required_env)}."
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": sorted(actions.keys()),
                    "description": "Which action to run.",
                },
                "params": {
                    "type": "object",
                    "description": "Action parameters (see action list above).",
                    "additionalProperties": True,
                },
                "confirm": {
                    "type": "boolean",
                    "default": False,
                    "description": "Set true to confirm a WRITE action.",
                },
            },
            "required": ["action"],
        }
    return {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["info"],
                       "description": "Only action available until a driver is implemented."},
            "params": {"type": "object", "additionalProperties": True},
            "confirm": {"type": "boolean", "default": False},
        },
        "required": ["action"],
    }

"""Self-awareness — report the runtime's actual state from its filesystem.

Grounds self-referential answers ("what can you do?") in the real registry:
skill counts, executable drivers, versions, and environment facts.
"""
from __future__ import annotations

import platform
import sys

from ..driver import ActionDef

SKILL = "self-awareness"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — introspects the running runtime."


async def get_runtime_info(params: dict) -> dict:
    from ..registry import load_registry
    try:
        from ..server import __version__
    except Exception:
        __version__ = "unknown"
    reg = load_registry()
    implemented = sorted(n for n, e in reg.items() if e.implemented)
    return {"status": "ok",
            "runtime_version": __version__,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "total_skills": len(reg),
            "executable_drivers": len(implemented),
            "catalog_only": sorted(set(reg) - set(implemented)),
            "executable": implemented}


async def describe_skill(params: dict) -> dict:
    from ..registry import load_registry
    entry = load_registry().get(params["skill"])
    if entry is None:
        return {"status": "ok", "found": False}
    return {"status": "ok", "found": True, "skill": entry.name,
            "implemented": entry.implemented,
            "actions": list(entry.actions.keys()),
            "required_env": entry.required_env}


ACTIONS = {
    "get_runtime_info": ActionDef("Report real runtime facts: versions, skill counts, driver list.",
        {}, [], get_runtime_info),
    "describe_skill": ActionDef("Describe one skill's real capabilities.",
        {"skill": {"type": "string"}}, ["skill"], describe_skill),
}

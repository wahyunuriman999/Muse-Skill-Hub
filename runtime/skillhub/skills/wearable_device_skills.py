"""Wearable device skills — discover wearable-related capabilities.

Introspects the live skill registry and surfaces the skills that work with
wearables and health data (withings, peloton, apple-healthkit,
google-health-connect, wearables-comms, ...). Real registry introspection.
"""
from __future__ import annotations

from ..driver import ActionDef

SKILL = "wearable-device-skills"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — introspects the live registry."

_WEARABLE_HINTS = ("withings", "peloton", "apple-healthkit", "google-health-connect",
                   "wearables-comms", "health")


async def discover(params: dict) -> dict:
    from ..registry import load_registry
    reg = load_registry()
    found = []
    for name, entry in sorted(reg.items()):
        if any(h in name for h in _WEARABLE_HINTS):
            found.append({"skill": name, "implemented": entry.implemented,
                          "actions": list(entry.actions.keys())})
    return {"status": "ok", "wearable_skills": found}


ACTIONS = {
    "discover": ActionDef("List wearable/health-related skills and their actions.",
        {}, [], discover),
}

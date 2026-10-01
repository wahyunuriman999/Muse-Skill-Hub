"""Agent library — LOCAL agent registry reference implementation.

Register, list, and describe agent definitions in a local JSON registry.
Reference implementation — not connected to any production agent backend.
"""
from __future__ import annotations

import time

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "agent-library"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "agents"


def _load() -> dict:
    return read_json(_STORE, {})


async def register_agent(params: dict) -> dict:
    agents = _load()
    name = params["name"]
    agents[name] = {"name": name, "description": params.get("description", ""),
                    "capabilities": params.get("capabilities", []),
                    "registered_at": int(time.time())}
    write_json(_STORE, agents)
    return {"status": "ok", "agent": agents[name]}


async def list_agents(params: dict) -> dict:
    return {"status": "ok", "agents": list(_load().values())}


async def get_agent(params: dict) -> dict:
    agent = _load().get(params["name"])
    if not agent:
        raise SkillError(SKILL, "not_found", "No such agent.")
    return {"status": "ok", "agent": agent}


async def remove_agent(params: dict) -> dict:
    agents = _load()
    if params["name"] not in agents:
        raise SkillError(SKILL, "not_found", "No such agent.")
    del agents[params["name"]]
    write_json(_STORE, agents)
    return {"status": "ok", "removed": params["name"]}


ACTIONS = {
    "register_agent": ActionDef("Register an agent definition (needs confirm=true).",
        {"name": {"type": "string"}, "description": {"type": "string"},
         "capabilities": {"type": "array", "items": {"type": "string"}}},
        ["name"], register_agent, write=True),
    "list_agents": ActionDef("List registered agents.", {}, [], list_agents),
    "get_agent": ActionDef("Describe one agent.",
        {"name": {"type": "string"}}, ["name"], get_agent),
    "remove_agent": ActionDef("Remove an agent (needs approval: irreversible).",
        {"name": {"type": "string"}}, ["name"], remove_agent, risk="destructive"),
}

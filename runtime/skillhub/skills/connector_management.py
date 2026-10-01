"""Connector management — LOCAL connector registry reference implementation.

Tracks third-party connector configurations (provider, auth type, status) in a
local JSON registry. This manages configuration records — it does not perform
OAuth flows itself. Reference implementation; swap the backend for production.
"""
from __future__ import annotations

import time

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "connector-management"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "connectors"


def _load() -> dict:
    return read_json(_STORE, {})


async def list_connectors(params: dict) -> dict:
    return {"status": "ok", "connectors": list(_load().values())}


async def get_connector(params: dict) -> dict:
    c = _load().get(params["provider"])
    if not c:
        raise SkillError(SKILL, "not_found", "No such connector.")
    return {"status": "ok", "connector": c}


async def set_connector(params: dict) -> dict:
    connectors = _load()
    connectors[params["provider"]] = {
        "provider": params["provider"], "auth_type": params.get("auth_type", "oauth"),
        "status": params.get("status", "configured"),
        "scopes": params.get("scopes", []), "updated_at": int(time.time())}
    write_json(_STORE, connectors)
    return {"status": "ok", "connector": connectors[params["provider"]]}


async def remove_connector(params: dict) -> dict:
    connectors = _load()
    connectors.pop(params["provider"], None)
    write_json(_STORE, connectors)
    return {"status": "ok", "removed": params["provider"]}


ACTIONS = {
    "list_connectors": ActionDef("List connector configurations.", {}, [], list_connectors),
    "get_connector": ActionDef("Get one connector's configuration.",
        {"provider": {"type": "string"}}, ["provider"], get_connector),
    "set_connector": ActionDef("Add/update a connector configuration (needs confirm=true).",
        {"provider": {"type": "string"}, "auth_type": {"type": "string"},
         "status": {"type": "string"}, "scopes": {"type": "array", "items": {"type": "string"}}},
        ["provider"], set_connector, write=True),
    "remove_connector": ActionDef("Remove a connector configuration (needs approval).",
        {"provider": {"type": "string"}}, ["provider"], remove_connector, write=True),
}

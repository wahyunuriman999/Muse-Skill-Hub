"""Paired devices — LOCAL device registry reference implementation.

Register, list, and unpair devices in a local JSON registry. Reference
implementation of the paired-devices interface — command execution against real
devices requires a device agent; swap the backend for production use.
"""
from __future__ import annotations

import time

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "paired-devices"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "devices"


def _load() -> dict:
    return read_json(_STORE, {})


async def register_device(params: dict) -> dict:
    devices = _load()
    devices[params["device_id"]] = {
        "device_id": params["device_id"], "name": params.get("name", ""),
        "platform": params.get("platform", ""), "paired_at": int(time.time())}
    write_json(_STORE, devices)
    return {"status": "ok", "device": devices[params["device_id"]]}


async def list_devices(params: dict) -> dict:
    return {"status": "ok", "devices": list(_load().values())}


async def unpair_device(params: dict) -> dict:
    devices = _load()
    if params["device_id"] not in devices:
        raise SkillError(SKILL, "not_found", "No such device.")
    del devices[params["device_id"]]
    write_json(_STORE, devices)
    return {"status": "ok", "unpaired": params["device_id"]}


ACTIONS = {
    "register_device": ActionDef("Register (pair) a device (needs confirm=true).",
        {"device_id": {"type": "string"}, "name": {"type": "string"},
         "platform": {"type": "string", "description": "e.g. android, ios, linux"}},
        ["device_id"], register_device, write=True),
    "list_devices": ActionDef("List paired devices.", {}, [], list_devices),
    "unpair_device": ActionDef("Unpair a device (needs confirm=true).",
        {"device_id": {"type": "string"}}, ["device_id"], unpair_device, write=True),
}

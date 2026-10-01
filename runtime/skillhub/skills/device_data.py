"""Device data — LOCAL cached device-data store.

Reads cached contacts/calendar snapshots from the local store and can delete
the local copy. Use import_snapshot to load a JSON snapshot exported from a device.
Reference implementation — not connected to any device sync backend.
"""
from __future__ import annotations

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "device-data"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "device-data"


def _load() -> dict:
    return read_json(_STORE, {"contacts": [], "calendar": []})


async def import_snapshot(params: dict) -> dict:
    data = {"contacts": params.get("contacts", []),
            "calendar": params.get("calendar", [])}
    write_json(_STORE, data)
    return {"status": "ok", "contacts": len(data["contacts"]),
            "calendar_events": len(data["calendar"])}


async def get_contacts(params: dict) -> dict:
    contacts = _load()["contacts"]
    if params.get("query"):
        q = params["query"].lower()
        contacts = [c for c in contacts if q in str(c).lower()]
    return {"status": "ok", "contacts": contacts[: int(params.get("limit", 50))]}


async def get_calendar(params: dict) -> dict:
    return {"status": "ok",
            "events": _load()["calendar"][: int(params.get("limit", 50))]}


async def delete_local_copy(params: dict) -> dict:
    write_json(_STORE, {"contacts": [], "calendar": []})
    return {"status": "ok", "deleted": "local device-data copy"}


ACTIONS = {
    "import_snapshot": ActionDef("Import a contacts/calendar snapshot (needs confirm=true).",
        {"contacts": {"type": "array", "items": {"type": "object"}},
         "calendar": {"type": "array", "items": {"type": "object"}}},
        [], import_snapshot, write=True),
    "get_contacts": ActionDef("Read cached contacts.",
        {"query": {"type": "string"}, "limit": {"type": "integer", "default": 50}},
        [], get_contacts),
    "get_calendar": ActionDef("Read cached calendar events.",
        {"limit": {"type": "integer", "default": 50}}, [], get_calendar),
    "delete_local_copy": ActionDef("Delete the local copy (needs approval: irreversible).",
        {}, [], delete_local_copy, risk="destructive"),
}

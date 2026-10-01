"""Data control — local data rights for skillhub-local data.

Explains what this runtime stores locally, exports it as a zip archive, and
deletes local copies on request. Operates on the local store (~/.skillhub-local/).
"""
from __future__ import annotations

import shutil

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import data_dir

SKILL = "data-control"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — manages the runtime's local data directory."

WHAT = ("This runtime stores only local JSON/SQLite records under "
        "~/.skillhub-local/ (override: SKILLHUB_LOCAL_DIR): vault secrets "
        "(encrypted), feed posts, ideas, goals, approvals, device/connector "
        "registries. No chat history or credentials leave the machine; provider "
        "API calls go directly from this machine to each provider.")


async def explain_collection(params: dict) -> dict:
    return {"status": "ok", "data_collection": WHAT}


async def export_data(params: dict) -> dict:
    d = data_dir()
    dest = str(d / "export.zip")
    shutil.make_archive(str(d / "export"), "zip", d)
    return {"status": "ok", "export_path": dest}


async def delete_data(params: dict) -> dict:
    scope = params.get("scope", "all")
    d = data_dir()
    if scope == "all":
        for p in d.iterdir():
            if p.name == "export.zip":
                continue
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
        return {"status": "ok", "deleted": "all local data"}
    target = d / f"{scope}.json"
    if not target.exists():
        raise SkillError(SKILL, "not_found", f"No local store named '{scope}'.")
    target.unlink()
    return {"status": "ok", "deleted": scope}


ACTIONS = {
    "explain_collection": ActionDef("Explain what data this runtime collects.",
        {}, [], explain_collection),
    "export_data": ActionDef("Export all local data as a zip archive.",
        {}, [], export_data),
    "delete_data": ActionDef("Delete local data (scope=all or a store name; needs confirm=true).",
        {"scope": {"type": "string", "default": "all",
                   "description": "all, or e.g. feed, ideas, goals, vault.enc"}},
        [], delete_data, write=True),
}

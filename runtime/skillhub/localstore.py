"""Local JSON store helper for reference-implementation drivers.

Drivers for Muse platform capabilities (vault, feed, ideas, permissions, ...)
have no public cloud API. They run as honest LOCAL reference implementations:
real logic, real local storage under ~/.skillhub-local/ (override with
SKILLHUB_LOCAL_DIR). Every such driver documents this in its SETUP_HELP —
swap the storage backend for production use.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def data_dir() -> Path:
    d = Path(os.environ.get("SKILLHUB_LOCAL_DIR", Path.home() / ".skillhub-local"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(name: str, default):
    p = data_dir() / f"{name}.json"
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(name: str, data) -> None:
    p = data_dir() / f"{name}.json"
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


LOCAL_NOTE = (
    "Local reference implementation: real logic with local file storage "
    "(~/.skillhub-local/, override with SKILLHUB_LOCAL_DIR). "
    "It does not connect to any cloud backend — swap the storage layer for production."
)

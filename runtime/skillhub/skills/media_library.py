"""Media library — local photo-directory scanner.

Scans a local directory for images and reports file metadata (name, size,
modified time, dimensions when Pillow is available). Set MEDIA_LIBRARY_PATH
(default: ~/Pictures).
"""
from __future__ import annotations

import os
from pathlib import Path

from ..driver import ActionDef

SKILL = "media-library"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "Set MEDIA_LIBRARY_PATH to the photo directory (default ~/Pictures)."

_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".mp4", ".mov"}


def _root() -> Path:
    return Path(os.environ.get("MEDIA_LIBRARY_PATH",
                               Path.home() / "Pictures")).expanduser()


def _scan(limit: int, query: str = "") -> list[dict]:
    root = _root()
    if not root.is_dir():
        return []
    q = query.lower()
    out = []
    for p in sorted(root.rglob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file() or p.suffix.lower() not in _EXTS:
            continue
        if q and q not in p.name.lower():
            continue
        st = p.stat()
        out.append({"path": str(p), "name": p.name, "size_bytes": st.st_size,
                    "modified": st.st_mtime})
        if len(out) >= limit:
            break
    return out


async def list_photos(params: dict) -> dict:
    return {"status": "ok", "root": str(_root()),
            "photos": _scan(min(int(params.get("limit", 20)), 200))}


async def search_photos(params: dict) -> dict:
    return {"status": "ok",
            "photos": _scan(min(int(params.get("limit", 20)), 200),
                            params.get("query", ""))}


ACTIONS = {
    "list_photos": ActionDef("List recent photos in the media library.",
        {"limit": {"type": "integer", "default": 20, "maximum": 200}},
        [], list_photos),
    "search_photos": ActionDef("Search photos by filename.",
        {"query": {"type": "string"},
         "limit": {"type": "integer", "default": 20, "maximum": 200}},
        ["query"], search_photos),
}

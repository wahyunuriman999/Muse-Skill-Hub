"""Personal feed — LOCAL feed-store reference implementation.

Real post storage with a local JSON store. Reference implementation of the
personal Feed interface — not connected to any production feed backend.
Swap the storage backend for production use.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "personal-feed"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "feed"


async def publish_post(params: dict) -> dict:
    posts = read_json(_STORE, [])
    post = {"id": uuid.uuid4().hex[:8], "title": params["title"],
            "body": params.get("body", ""), "category": params.get("category", "general"),
            "published_at": int(time.time())}
    posts.insert(0, post)
    write_json(_STORE, posts[:200])
    return {"status": "ok", "post": post}


async def list_posts(params: dict) -> dict:
    posts = read_json(_STORE, [])
    return {"status": "ok", "posts": posts[: int(params.get("limit", 20))]}


ACTIONS = {
    "publish_post": ActionDef("Publish a feed post (needs confirm=true).",
        {"title": {"type": "string"}, "body": {"type": "string"},
         "category": {"type": "string", "default": "general"}},
        ["title"], publish_post, write=True),
    "list_posts": ActionDef("List feed posts, newest first.",
        {"limit": {"type": "integer", "default": 20}},
        [], list_posts),
}

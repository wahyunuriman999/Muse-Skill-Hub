"""Share ideas — publish portable idea cards as local markdown files.

Writes a portable idea card (title, pitch, steps) to the local ideas directory
as markdown, ready to share or import elsewhere.
"""
from __future__ import annotations

import time
import uuid

from ..driver import ActionDef
from ..localstore import data_dir

SKILL = "share-ideas"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — writes markdown files locally."


async def publish_idea(params: dict) -> dict:
    idea_id = uuid.uuid4().hex[:8]
    out_dir = data_dir() / "shared-ideas"
    out_dir.mkdir(parents=True, exist_ok=True)
    steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(params.get("steps", [])))
    md = (f"# {params['title']}\n\n"
          f"**Idea ID:** {idea_id}  \n"
          f"**Published:** {time.strftime('%Y-%m-%d')}\n\n"
          f"## Pitch\n\n{params.get('pitch', '')}\n\n"
          f"## Steps\n\n{steps}\n")
    path = out_dir / f"{idea_id}.md"
    path.write_text(md, encoding="utf-8")
    return {"status": "ok", "idea_id": idea_id, "path": str(path)}


ACTIONS = {
    "publish_idea": ActionDef("Publish a portable idea card as markdown (needs confirm=true).",
        {"title": {"type": "string"}, "pitch": {"type": "string"},
         "steps": {"type": "array", "items": {"type": "string"}}},
        ["title"], publish_idea, write=True),
}

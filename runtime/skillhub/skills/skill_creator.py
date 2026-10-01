"""Skill creator — scaffold new skill directories with SKILL.md templates.

Generates a ready-to-fill skill folder (SKILL.md frontmatter + README) under
the local new-skills directory. This creates the skill *definition*; to add a
runnable driver, implement runtime/skillhub/skills/<name>.py following the
driver contract (see runtime/README.md).
"""
from __future__ import annotations

import re

from ..driver import ActionDef
from ..localstore import data_dir

SKILL = "skill-creator"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — writes skill scaffolds locally."

_TEMPLATE = """---
name: {name}
description: "{description}"
---

# {title}

## Purpose

{description}

## Workflow

1. ...
2. ...

## Notes

- ...
"""


async def scaffold_skill(params: dict) -> dict:
    name = re.sub(r"[^a-z0-9-]", "-", params["name"].lower()).strip("-")
    title = params.get("title") or name.replace("-", " ").title()
    out = data_dir() / "new-skills" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "SKILL.md").write_text(
        _TEMPLATE.format(name=name, title=title,
                         description=params.get("description", "")),
        encoding="utf-8")
    (out / "README.md").write_text(f"# {title}\n\n{params.get('description', '')}\n",
                                   encoding="utf-8")
    return {"status": "ok", "skill": name, "path": str(out),
            "files": ["SKILL.md", "README.md"]}


ACTIONS = {
    "scaffold_skill": ActionDef("Scaffold a new skill folder with templates (needs confirm=true).",
        {"name": {"type": "string", "description": "kebab-case name"},
         "title": {"type": "string"}, "description": {"type": "string"}},
        ["name"], scaffold_skill, write=True),
}

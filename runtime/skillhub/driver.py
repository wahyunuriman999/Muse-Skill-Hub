"""Driver contract shared by every skill driver module.

A driver module must define:
    SKILL: str            - skill name, matches skills/<name>/
    REQUIRED_ENV: list    - env vars needed (empty = works without credentials)
    SETUP_HELP: str       - shown when credentials are missing
    ACTIONS: dict         - action name -> ActionDef
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class ActionDef:
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)  # JSON-schema properties
    required: list[str] = field(default_factory=list)
    handler: Callable[[dict], Awaitable[dict]] | None = None
    write: bool = False  # write actions need confirm=true (read/write isolation)

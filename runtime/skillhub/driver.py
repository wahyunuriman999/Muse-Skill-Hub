"""Driver contract shared by every skill driver module (v2).

A driver module must define:
    SKILL: str            - skill name, matches skills/<name>/
    REQUIRED_ENV: list    - env vars needed (empty = works without credentials)
    SETUP_HELP: str       - shown when credentials are missing
    ACTIONS: dict         - action name -> ActionDef

Risk levels (used by the policy + approval engines):
    read          - no side effects
    write         - ordinary state change (needs approval)
    sensitive     - reads/writes private data (needs approval)
    destructive   - deletes or irreversibly changes data (needs approval)
    communication - sends messages/email externally (needs approval)
    financial     - moves money or changes billing (needs approval)
    account       - changes account access/settings (needs approval)
    device        - controls physical devices (needs approval)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

RISK_LEVELS = ("read", "write", "sensitive", "destructive",
               "communication", "financial", "account", "device")


@dataclass
class ActionDef:
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)  # JSON-schema properties
    required: list[str] = field(default_factory=list)
    handler: Callable[[dict], Awaitable[dict]] | None = None
    write: bool = False  # legacy flag; prefer `risk`
    risk: str = ""  # one of RISK_LEVELS; defaults to "write" if write else "read"
    output_schema: dict[str, Any] = field(default_factory=dict)  # JSON schema of result
    idempotent: bool = True  # safe to retry with the same idempotency key
    sensitive_params: list[str] = field(default_factory=list)  # never audit-logged raw

    def __post_init__(self):
        if not self.risk:
            self.risk = "write" if self.write else "read"
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unknown risk level: {self.risk}")
        # write=True actions are never pure reads
        if self.write and self.risk == "read":
            self.risk = "write"

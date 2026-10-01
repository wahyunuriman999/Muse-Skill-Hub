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
    # NOTE on terminology: this does NOT mean "the operation is mathematically
    # idempotent". It means "the runtime may deduplicate this action with a
    # client-supplied idempotency key" (reservation before execution, atomic
    # commit after). Renamed from `idempotent` in v2.1 for exactly this reason.
    supports_idempotency_key: bool = True
    sensitive_params: list[str] = field(default_factory=list)  # never audit-logged raw
    required_scopes: list[str] = field(default_factory=list)  # credential scopes
    strict: bool = True  # reject unknown params (schema is the source of truth)

    # deprecated alias for `supports_idempotency_key` (v2.0 name)
    idempotent: bool | None = None

    # True when the driver explicitly passed risk=... (vs. the
    # write/read default). The manifest generator preserves hand-tuned
    # manifest risks for actions whose driver did not declare one.
    risk_explicit: bool = False

    def __post_init__(self):
        self.risk_explicit = bool(self.risk)
        if not self.risk:
            self.risk = "write" if self.write else "read"
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"unknown risk level: {self.risk}")
        # write=True actions are never pure reads
        if self.write and self.risk == "read":
            self.risk = "write"
        if self.idempotent is not None:
            # explicit v2.0-style kwarg wins, then clear the alias
            self.supports_idempotency_key = self.idempotent
            self.idempotent = None

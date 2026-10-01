"""Policy engine — risk-based gate between the LLM and the drivers.

Architecture::

    LLM → skill → action → PolicyEngine → ALLOW / APPROVAL_REQUIRED / DENY
                                        → driver

Default policy:
- risk=read            → ALLOW
- risk=write           → APPROVAL_REQUIRED (legacy ``confirm=true`` accepted)
- risk=sensitive/destructive/communication/financial/account/device
                       → APPROVAL_REQUIRED (real approval_id required;
                         bare ``confirm=true`` is NOT enough)

Per-action risk lives in ``skillhub/catalog/<name>/manifest.yaml`` (canonical source
of truth), applied by ``registry.load_registry()``. A driver may still
declare ``risk=`` directly on ActionDef as the default the manifest
overrides.

A custom policy file (JSON) can be pointed at with SKILLHUB_POLICY_FILE::

    {"rules": {"gmail.send_message": "deny", "github.*": "approval_required"},
     "default": "approval_required"}

Rule values: allow | approval_required | deny. ``*`` wildcards supported.
"""
from __future__ import annotations

import fnmatch
import json
import os

# NOTE (v2.1): per-action risk is no longer hardcoded here. It lives in
# skillhub/catalog/<name>/manifest.yaml (canonical source of truth), applied by
# registry.load_registry(). This function stays as a compatibility shim:
# the "driver_risk" it receives is already manifest-resolved.


# Risks that ALWAYS need a real approval_id (bare confirm=true is not enough)
STRICT_RISKS = frozenset({
    "sensitive", "destructive", "communication", "financial", "account", "device",
})


def risk_for(skill: str, action: str, declared: str) -> str:
    """Compatibility shim: ``declared`` is already manifest-resolved."""
    return declared or "read"


class PolicyEngine:
    def __init__(self, rules: dict | None = None):
        self.rules = rules or {}
        custom = os.environ.get("SKILLHUB_POLICY_FILE")
        if custom and os.path.exists(custom):
            with open(custom, encoding="utf-8") as f:
                self.rules = json.load(f).get("rules", {})

    def evaluate(self, skill: str, action: str, risk: str) -> str:
        """Return allow | approval_required | deny."""
        key = f"{skill}.{action}"
        for pattern, verdict in self.rules.items():
            if fnmatch.fnmatch(key, pattern) or fnmatch.fnmatch(skill, pattern):
                return verdict
        if risk == "read":
            return "allow"
        if risk in STRICT_RISKS:
            return "approval_required"
        return "approval_required"  # plain write also needs approval


DEFAULT_POLICY = PolicyEngine()

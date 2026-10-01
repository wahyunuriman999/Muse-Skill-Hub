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

Per-action risk overrides live in RISK_OVERRIDES below so drivers don't
all need editing; a driver may also declare ``risk=`` directly on ActionDef.

A custom policy file (JSON) can be pointed at with SKILLHUB_POLICY_FILE::

    {"rules": {"gmail.send_message": "deny", "github.*": "approval_required"},
     "default": "approval_required"}

Rule values: allow | approval_required | deny. ``*`` wildcards supported.
"""
from __future__ import annotations

import fnmatch
import json
import os

# skill.action -> risk level (curated from real driver actions;
# everything else defaults from the write flag)
RISK_OVERRIDES: dict[str, str] = {
    # financial
    "stripe.create_payment_link": "financial",
    "duffel.create_order": "financial",
    "wallet.add_payment_method": "financial",
    # communication
    "gmail.send_message": "communication",
    "outlook-mail.send_mail": "communication",
    "slack.send_message": "communication",
    "messenger.send_message": "communication",
    "instagram-messages.send_message": "communication",
    "meta-threads.post_text": "communication",
    "voice-calls.make_call": "communication",
    "tts.synthesize": "communication",
    "zapier.trigger_zap": "communication",
    # destructive
    "muse_db.execute_write": "destructive",
    "forget.forget_fact": "destructive",
    "data-control.delete_data": "destructive",
    # sensitive reads
    "gmail.get_message": "sensitive",
    "secure-vault.reveal_secret": "sensitive",
    # account
    "connector-management.remove_connector": "account",
    # device
    "philips-hue.set_light": "device",
}

# Risks that need a REAL approval_id (bare confirm=true is not enough).
STRICT_RISKS = {"sensitive", "destructive", "communication",
                "financial", "account", "device"}


def risk_for(skill: str, action: str, declared: str) -> str:
    return RISK_OVERRIDES.get(f"{skill}.{action}", declared or "read")


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

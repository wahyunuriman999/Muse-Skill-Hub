"""Structured errors for the Muse Skill Hub runtime (v2 contract).

Every failure is returned as a machine-readable envelope so any LLM client
can understand what went wrong and what to do next — no silent failures,
no hallucinated successes.

Envelope::

    {
      "ok": false,
      "error": {
        "code": "RATE_LIMITED",
        "message": "human-readable, safe for the LLM",
        "retryable": true,
        "retry_after": 30
      },
      "meta": {
        "request_id": "9f2c…",
        "skill": "gmail",
        "action": "send_message"
      }
    }

Security rule: internal details (tracebacks, provider payloads, secret
values) NEVER go to the LLM. They go to the audit log only. Set
SKILLHUB_DEBUG=1 to include internal detail in the message during development.
"""
from __future__ import annotations

import os

_DEBUG = os.environ.get("SKILLHUB_DEBUG") == "1"


_LEGACY_CODES = {
    "not_found": "not_found",
    "missing_dependency": "internal_error",
    "missing dependency": "internal_error",
    "not_configured": "auth_required",
    "bad_export": "invalid_input",
    "dependency_missing": "internal_error",
    "cli_not_installed": "internal_error",
    "read_only": "permission_denied",
}


class SkillError(Exception):
    code = "internal_error"
    retryable = False

    def __init__(self, message: str = "", *legacy, code: str | None = None,
                 internal: str = "", retry_after: int | None = None,
                 skill: str = "", action: str = ""):
        # Legacy call shape: SkillError(SKILL, code, message) — still used by
        # older drivers. Map it onto the v2 contract.
        if legacy and len(legacy) == 2:
            skill, legacy_code, message = message, legacy[0], legacy[1]
            code = _LEGACY_CODES.get(str(legacy_code), "internal_error")
        if code:
            self.code = code
        self.public_message = message or "Skill error."
        self.internal = internal  # never sent to the LLM unless SKILLHUB_DEBUG=1
        self.retry_after = retry_after
        self.skill = skill
        self.action = action
        super().__init__(self.public_message)

    def to_dict(self) -> dict:
        """Legacy dict shape (kept for backward compatibility)."""
        d = {"status": "error", "code": self.code, "message": self._message()}
        if self.skill:
            d["skill"] = self.skill
        return d

    def _message(self) -> str:
        if _DEBUG and self.internal:
            return f"{self.public_message} [internal: {self.internal}]"
        return self.public_message

    def to_envelope(self, request_id: str = "") -> dict:
        err: dict = {"code": self.code, "message": self._message(),
                     "retryable": self.retryable}
        if self.retry_after is not None:
            err["retry_after"] = self.retry_after
        return {"ok": False, "error": err,
                "meta": {"request_id": request_id, "skill": self.skill,
                         "action": self.action}}


# --- auth -----------------------------------------------------------------

class CredentialsMissing(SkillError):
    code = "auth_required"

    def __init__(self, skill: str, env_vars: list[str], setup: str = ""):
        self.env_vars = env_vars
        self.setup = setup
        super().__init__(
            f"Skill '{skill}' needs credentials. "
            f"Set environment variable(s): {', '.join(env_vars)}. {setup}".strip(),
            skill=skill)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"missing_env": self.env_vars, "setup": self.setup})
        return d


class AuthExpired(SkillError):
    code = "auth_expired"
    retryable = False


# --- approval / policy ------------------------------------------------------

class ConfirmationRequired(SkillError):
    """Legacy simple confirmation gate (kept for backward compatibility)."""
    code = "approval_required"

    def __init__(self, skill: str, action: str, preview: dict | None = None,
                 approval_id: str = ""):
        self.preview = preview or {}
        self.approval_id = approval_id
        msg = (f"Write action '{skill}.{action}' needs explicit approval. "
               "Re-run with confirm=true, or approve the pending request.")
        if approval_id:
            msg += f" Pending approval id: {approval_id}."
        super().__init__(msg, skill=skill, action=action)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"action": self.action, "preview": self.preview})
        if self.approval_id:
            d["approval_id"] = self.approval_id
        return d


class ApprovalRequired(ConfirmationRequired):
    code = "approval_required"


class ApprovalExpired(SkillError):
    code = "approval_expired"


class ApprovalRevoked(SkillError):
    code = "approval_revoked"


class PolicyBlocked(SkillError):
    code = "policy_blocked"

    def __init__(self, skill: str, action: str, reason: str):
        super().__init__(f"Policy blocked '{skill}.{action}': {reason}",
                         skill=skill, action=action)


class PermissionDenied(SkillError):
    code = "permission_denied"


# --- input / contract --------------------------------------------------------

class InvalidInput(SkillError):
    code = "invalid_input"

    def __init__(self, skill: str, action: str, problems: list[str]):
        self.problems = problems
        super().__init__(
            f"Invalid input for '{skill}.{action}': " + "; ".join(problems),
            skill=skill, action=action)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"action": self.action, "problems": self.problems})
        return d


class DriverNotImplemented(SkillError):
    code = "driver_not_implemented"

    def __init__(self, skill: str):
        super().__init__(
            f"Skill '{skill}' is registered in the catalog but has no executable "
            f"driver yet. Implement it in runtime/skillhub/skills/{skill}.py "
            "following the driver template (see runtime/skillhub/skills/github.py).",
            skill=skill)


class IdempotencyConflict(SkillError):
    code = "idempotency_conflict"
    retryable = False


# --- upstream -----------------------------------------------------------------

class UpstreamError(SkillError):
    code = "upstream_error"
    retryable = True

    def __init__(self, skill: str, detail: str, *, action: str = ""):
        # `detail` may contain provider internals → keep it out of the LLM
        # message unless SKILLHUB_DEBUG=1.
        super().__init__(f"Upstream API error in '{skill}'.",
                         internal=detail, skill=skill, action=action)


class RateLimited(UpstreamError):
    code = "rate_limited"
    retryable = True

    def __init__(self, skill: str, retry_after: int | None = None, *, action: str = ""):
        SkillError.__init__(
            self, f"Rate limited by '{skill}' upstream.",
            internal=f"HTTP 429 retry_after={retry_after}",
            retry_after=retry_after, skill=skill, action=action)


class UpstreamUnavailable(UpstreamError):
    code = "upstream_unavailable"
    retryable = True


class Timeout(UpstreamError):
    code = "timeout"
    retryable = True

    def __init__(self, skill: str, *, action: str = ""):
        SkillError.__init__(self, f"Upstream request for '{skill}' timed out.",
                            skill=skill, action=action)


class NotFound(UpstreamError):
    code = "not_found"
    retryable = False


class Conflict(UpstreamError):
    code = "conflict"
    retryable = False


# --- storage -------------------------------------------------------------------

class StoreCorruptError(SkillError):
    code = "internal_error"

    def __init__(self, store: str, backup: str):
        super().__init__(
            f"Local store '{store}' is corrupt. A backup was saved to {backup}; "
            f"refusing to silently fall back to defaults.",
            internal=f"corrupt store: {store} -> backup {backup}")

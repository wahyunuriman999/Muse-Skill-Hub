"""Structured errors for the Muse Skill Hub runtime.

Every failure is returned as a machine-readable dict so any LLM client
can understand what went wrong and what to do next — no silent failures,
no hallucinated successes.
"""
from __future__ import annotations


class SkillError(Exception):
    code = "skill_error"

    def to_dict(self) -> dict:
        return {"status": "error", "code": self.code, "message": str(self)}


class CredentialsMissing(SkillError):
    code = "credentials_missing"

    def __init__(self, skill: str, env_vars: list[str], setup: str = ""):
        self.skill = skill
        self.env_vars = env_vars
        self.setup = setup
        super().__init__(
            f"Skill '{skill}' needs credentials. "
            f"Set environment variable(s): {', '.join(env_vars)}. {setup}".strip()
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"skill": self.skill, "missing_env": self.env_vars, "setup": self.setup})
        return d


class ConfirmationRequired(SkillError):
    code = "confirmation_required"

    def __init__(self, skill: str, action: str, preview: dict | None = None):
        self.skill = skill
        self.action = action
        self.preview = preview or {}
        super().__init__(
            f"Write action '{skill}.{action}' needs explicit confirmation. "
            "Re-run with confirm=true to proceed."
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"skill": self.skill, "action": self.action, "preview": self.preview})
        return d


class DriverNotImplemented(SkillError):
    code = "driver_not_implemented"

    def __init__(self, skill: str):
        self.skill = skill
        super().__init__(
            f"Skill '{skill}' is registered in the catalog but has no executable "
            f"driver yet. Implement it in runtime/skillhub/skills/{skill}.py "
            "following the driver template (see runtime/skillhub/skills/github.py)."
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"skill": self.skill})
        return d


class UpstreamError(SkillError):
    code = "upstream_error"

    def __init__(self, skill: str, detail: str):
        self.skill = skill
        super().__init__(f"Upstream API error in '{skill}': {detail}")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"skill": self.skill})
        return d

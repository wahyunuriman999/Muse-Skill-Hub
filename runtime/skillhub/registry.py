"""Skill registry: loads the catalog, validates input, enforces policy,
and dispatches actions (v2).

Execution pipeline::

    params → validate → policy → approval → idempotency → credentials
           → handler → audit

Every dispatch is audit-logged. Secrets are never logged raw.
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import approval, audit, localstore
from .driver import ActionDef
from .errors import (ApprovalRequired, DriverNotImplemented, IdempotencyConflict,
                     PolicyBlocked, SkillError, UpstreamError)
from .policy import DEFAULT_POLICY, STRICT_RISKS, PolicyEngine, risk_for
from .validate import validate_params

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"
RUNTIME_SKILLS = Path(__file__).resolve().parent / "skills"

# skill name -> python module name when they differ
MODULE_OVERRIDES = {
    "places-search": "places_search",
    # "threads" and "meta-threads" are the same Threads account skill;
    # both names share the real driver.
    "threads": "meta_threads",
}


@dataclass
class SkillEntry:
    name: str
    description: str
    implemented: bool
    actions: dict[str, ActionDef] = field(default_factory=dict)
    required_env: list[str] = field(default_factory=list)
    setup_help: str = ""
    version: str = "1.0.0"


def _frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip("'\"")
    return meta, text


def load_registry() -> dict[str, SkillEntry]:
    reg: dict[str, SkillEntry] = {}
    if not SKILLS_DIR.exists():
        return reg
    for md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        name = md.parent.name
        meta, _ = _frontmatter(md)
        entry = SkillEntry(
            name=name,
            description=meta.get("description", ""),
            implemented=False,
            version=meta.get("version", "1.0.0"),
        )
        mod_name = MODULE_OVERRIDES.get(name, name.replace("-", "_"))
        mod_path = RUNTIME_SKILLS / f"{mod_name}.py"
        if mod_path.exists():
            import importlib

            mod = importlib.import_module(f"skillhub.skills.{mod_name}")
            entry.implemented = True
            entry.actions = getattr(mod, "ACTIONS", {})
            entry.required_env = getattr(mod, "REQUIRED_ENV", [])
            entry.setup_help = getattr(mod, "SETUP_HELP", "")
        reg[name] = entry
    return reg


# --- capability discovery -----------------------------------------------------

def search_capabilities(registry: dict[str, SkillEntry], query: str,
                        top_k: int = 8) -> list[dict]:
    """Keyword search over the catalog → top-K candidates for dynamic loading."""
    terms = [t.lower() for t in query.split() if t]
    scored: list[tuple[int, SkillEntry]] = []
    for entry in registry.values():
        hay = " ".join([entry.name, entry.description,
                        *[a for a in entry.actions],
                        *[ad.description for ad in entry.actions.values()]]).lower()
        score = sum(3 if t in entry.name.lower() else 1 for t in terms if t in hay)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda s: -s[0])
    return [{"skill": e.name, "description": e.description,
             "implemented": e.implemented,
             "actions": sorted(e.actions),
             "tools": [action_tool_name(e.name, a) for a in sorted(e.actions)]}
            for _, e in scored[:top_k]]


# --- per-action MCP tools -------------------------------------------------------

def action_tool_name(skill: str, action: str) -> str:
    return f"{skill}_{action}".replace("-", "_")


def split_tool_name(registry: dict[str, SkillEntry], tool: str) -> tuple[str, str] | None:
    """Split 'skill_action' back into (skill, action): longest skill-prefix wins."""
    for skill in sorted(registry, key=len, reverse=True):
        prefix = skill.replace("-", "_") + "_"
        if tool.startswith(prefix):
            action = tool[len(prefix):]
            if action in registry[skill].actions:
                return skill, action
    return None


def action_schema(skill: str, action: str, action_def: ActionDef,
                  required_env: list[str]) -> dict:
    """Full JSON schema for one action tool — params are inlined, not opaque."""
    properties: dict[str, Any] = dict(action_def.parameters or {})
    required = list(action_def.required or [])
    if action_def.risk != "read":
        properties["confirm"] = {
            "type": "boolean", "default": False,
            "description": "Legacy simple confirmation for write actions. "
                           "Higher-risk actions need approval_id instead."}
        properties["approval_id"] = {
            "type": "string",
            "description": "Approval id (apr_…) from the approval engine. "
                           "Bound to this exact skill/action/parameters, "
                           "single-use, expires after 10 minutes."}
        properties["idempotency_key"] = {
            "type": "string",
            "description": "Client-supplied key: repeat calls with the same key "
                           "return the first result instead of re-executing."}
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
    return schema


def action_tool_description(skill: str, action: str, action_def: ActionDef,
                            required_env: list[str], implemented: bool) -> str:
    if not implemented:
        return (f"[{skill}] catalog only — driver not implemented yet. "
                f"Action '{action}' is documented but not executable.")
    desc = f"[{skill}] {action_def.description}"
    desc += f"\nRisk: {action_def.risk}."
    if action_def.risk != "read":
        desc += " Needs approval (approval_id, or confirm=true for plain writes)."
    if required_env:
        desc += f" Needs env: {', '.join(required_env)}."
    if action_def.output_schema:
        desc += " Structured output (see output schema)."
    return desc


def mcp_tools(registry: dict[str, SkillEntry]) -> list[dict]:
    """Every executable action becomes its own MCP tool.

    Tool names look like ``github_search_repositories`` — the LLM picks a
    precise tool instead of stuffing an action name into a string param.
    """
    tools = []
    for name, entry in registry.items():
        if not entry.implemented:
            continue
        for action, ad in entry.actions.items():
            tools.append({
                "name": action_tool_name(name, action),
                "description": action_tool_description(
                    name, action, ad, entry.required_env, True),
                "inputSchema": action_schema(name, action, ad, entry.required_env),
            })
    tools.append({
        "name": "skillhub_search_capabilities",
        "description": "Search the skill catalog by keyword. Returns top-K "
                       "matching skills with their tool names. Use for dynamic "
                       "capability discovery instead of guessing tool names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "What you want to do, e.g. 'send email'."},
                "top_k": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    })
    return tools


def tool_schema(entry: SkillEntry) -> dict:
    """Legacy per-skill overview schema (kept for backward compatibility)."""
    actions = sorted(entry.actions)
    return {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": actions or ["info"],
                       "description": "Which action to run."},
            "params": {"type": "object", "additionalProperties": True},
            "confirm": {"type": "boolean", "default": False},
        },
        "required": ["action"],
    }


# --- dispatch --------------------------------------------------------------------

_IDEMPOTENCY_STORE = "idempotency"


def _missing_env(entry: SkillEntry) -> list[str]:
    return [v for v in entry.required_env if not os.environ.get(v)]


def _idem_get(key: str) -> dict | None:
    return localstore.read_json(_IDEMPOTENCY_STORE, {}).get(key)


def _idem_put(key: str, record: dict) -> None:
    data = localstore.read_json(_IDEMPOTENCY_STORE, {})
    data[key] = record
    # keep the store bounded
    if len(data) > 2000:
        data = dict(sorted(data.items(),
                           key=lambda kv: kv[1].get("created_at", 0))[-2000:])
    localstore.write_json(_IDEMPOTENCY_STORE, data)


async def dispatch(entry: SkillEntry, action: str, params: dict,
                   confirm: bool = False, *,
                   approval_id: str | None = None,
                   idempotency_key: str | None = None,
                   request_id: str | None = None,
                   actor: str = "local-user",
                   policy: PolicyEngine | None = None) -> dict:
    """Execute one skill action through the full v2 pipeline."""
    request_id = request_id or uuid.uuid4().hex[:12]
    started = time.monotonic()
    policy = policy or DEFAULT_POLICY
    params = params or {}
    action_def = None
    audit_base = {"request_id": request_id, "actor": actor,
                  "skill": entry.name, "action": action}

    def _audit(result: str, **extra):
        sensitive = tuple(action_def.sensitive_params) if action_def else ()
        preview, params_hash = audit.redact_params(params, sensitive)
        audit.log({**audit_base, "params_hash": params_hash,
                   "params_preview": preview, "result": result,
                   "duration_ms": int((time.monotonic() - started) * 1000),
                   **extra})

    try:
        if not entry.implemented or action not in entry.actions:
            raise DriverNotImplemented(entry.name)
        action_def = entry.actions[action]

        # 1. input validation — before anything else
        validate_params(entry.name, action, action_def.parameters,
                        action_def.required, params)

        # 2. policy
        risk = risk_for(entry.name, action, action_def.risk)
        verdict = policy.evaluate(entry.name, action, risk)
        if verdict == "deny":
            raise PolicyBlocked(entry.name, action,
                                f"policy rule denies {entry.name}.{action}")

        # 3. approval for anything riskier than read
        approval_used = ""
        if verdict == "approval_required":
            if approval_id:
                approval.consume(approval_id, entry.name, action, params)
                approval_used = approval_id
            elif confirm and risk == "write":
                pass  # legacy simple confirmation for plain writes
            else:
                pending = approval.request_approval(
                    entry.name, action, params, risk=risk,
                    preview={k: params.get(k) for k in action_def.required})
                raise ApprovalRequired(entry.name, action,
                                       preview=pending["preview"],
                                       approval_id=pending["approval_id"])

        # 4. idempotency — same key, same call → first result, no re-execution
        idem_hit = False
        if risk != "read" and action_def.idempotent and idempotency_key:
            existing = _idem_get(idempotency_key)
            if existing:
                import hashlib, json as _json
                phash = hashlib.sha256(
                    _json.dumps(params, sort_keys=True, default=str).encode()
                ).hexdigest()
                if (existing.get("skill"), existing.get("action")) != \
                        (entry.name, action) or existing.get("params_hash") != phash:
                    raise IdempotencyConflict(
                        f"Idempotency key '{idempotency_key}' was already used "
                        f"for a different call.")
                idem_hit = True
                result = dict(existing["result"])
                result["deduplicated"] = True
                _audit("deduplicated", risk=risk, approval_id=approval_used,
                       idempotency_key=idempotency_key)
                return result

        # 5. credentials
        missing = _missing_env(entry)
        if missing:
            from .errors import CredentialsMissing
            raise CredentialsMissing(entry.name, missing, entry.setup_help)

        # 6. execute
        try:
            result = await action_def.handler(dict(params))
        except SkillError:
            raise
        except Exception as exc:  # never leak tracebacks as success
            raise UpstreamError(entry.name, f"{type(exc).__name__}: {exc}",
                                action=action) from exc

        if risk != "read" and action_def.idempotent and idempotency_key and not idem_hit:
            import hashlib, json as _json
            _idem_put(idempotency_key, {
                "skill": entry.name, "action": action,
                "params_hash": hashlib.sha256(
                    _json.dumps(params, sort_keys=True, default=str).encode()
                ).hexdigest(),
                "result": result if isinstance(result, dict) else {"result": result},
                "created_at": int(time.time()),
            })

        _audit("success", risk=risk, approval_id=approval_used,
               idempotency_key=idempotency_key or "")
        if isinstance(result, dict):
            result = dict(result)
            result.setdefault("meta", {})["request_id"] = request_id
            return result
        return {"status": "ok", "result": result,
                "meta": {"request_id": request_id}}
    except SkillError as exc:
        _audit("error", risk=locals().get("risk", ""),
               error_code=exc.code,
               error_internal=exc.internal if exc.internal else "")
        raise

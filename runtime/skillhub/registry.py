"""Skill registry: loads the catalog, validates input, enforces policy,
and dispatches actions (v2.1).

Execution pipeline::

    params → validate → policy → approval → credentials → scope check
           → idempotency reserve → handler → output validation
           → idempotency commit → audit

The manifest (``skillhub/catalog/<name>/manifest.yaml``) is the canonical source of
truth for per-action risk: the registry applies manifest risk over driver
defaults at load time. Approval consumption and idempotency reservation
are atomic (single file-locked critical section each). Every dispatch is
audit-logged. Secrets are never logged raw.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import approval, audit, localstore, wal
from .driver import RISK_LEVELS, ActionDef
from .errors import (ApprovalRequired, DriverNotImplemented, IdempotencyConflict,
                     PolicyBlocked, SkillError, UpstreamError)
from .policy import DEFAULT_POLICY, STRICT_RISKS, PolicyEngine, risk_for
from .validate import validate_output, validate_params

SKILLS_DIR = Path(__file__).resolve().parent / "catalog"
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


def _manifest_risks(name: str) -> dict[str, str]:
    """Per-action risk from the skill manifest — the canonical source of truth.

    The manifest is generated from drivers + policy, but at runtime the
    manifest wins: ``manifest → driver → MCP → policy`` all agree because
    they all read this value.
    """
    path = SKILLS_DIR / name / "manifest.yaml"
    risks: dict[str, str] = {}
    if not path.exists():
        return risks
    try:
        import yaml
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return risks
    for item in doc.get("actions") or []:
        if isinstance(item, dict) and item.get("name") and item.get("risk"):
            risk = str(item["risk"])
            if risk not in RISK_LEVELS:
                raise ValueError(
                    f"manifest {name}: unknown risk level '{risk}' "
                    f"for action '{item['name']}'")
            risks[str(item["name"])] = risk
    return risks


def load_registry(apply_manifest_risks: bool = True) -> dict[str, SkillEntry]:
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
            # manifest is the canonical source of truth for per-action risk
            # at RUNTIME. The manifest generator bypasses this (it regenerates
            # manifests FROM the drivers), so driver edits propagate.
            if apply_manifest_risks:
                manifest_risks = _manifest_risks(name)
                for aname, ad in entry.actions.items():
                    manifest_risk = manifest_risks.get(aname)
                    if manifest_risk:
                        ad.risk = manifest_risk
        reg[name] = entry
    return reg


# --- capability discovery -----------------------------------------------------

import math as _math
import re as _re

_TOKEN_RE = _re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _capability_corpus(registry: dict[str, SkillEntry]) -> dict[str, str]:
    docs = {}
    for name, entry in registry.items():
        name_words = entry.name.replace("-", " ")
        docs[name] = " ".join([
            # skill name repeated: an exact name match should outrank a
            # description-only match (same 3x boost the old scorer used)
            name_words, name_words, name_words,
            entry.description,
            *[a.replace("_", " ") for a in entry.actions],
            *[ad.description for ad in entry.actions.values()],
        ])
    return docs


def search_capabilities(registry: dict[str, SkillEntry], query: str,
                        top_k: int = 8) -> list[dict]:
    """Relevance-ranked capability search (TF-IDF cosine, no external deps).

    Each skill is a document (name + description + action names +
    descriptions); the query is scored by TF-IDF cosine similarity. This
    is lexical relevance ranking — better than substring matching, but not
    semantic embeddings. Dynamic code loading is still out of scope:
    results name tools that already exist in the MCP server.
    """
    docs = _capability_corpus(registry)
    names = list(docs)
    # document frequency
    df: dict[str, int] = {}
    doc_tokens: dict[str, list[str]] = {}
    for n in names:
        toks = _tokens(docs[n])
        doc_tokens[n] = toks
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n_docs = max(1, len(names))
    idf = {t: _math.log(n_docs / (1 + c)) for t, c in df.items()}

    def vec(toks: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        total = max(1, len(toks))
        return {t: (c / total) * idf.get(t, 0.0) for t, c in tf.items()}

    def cosine(a: dict[str, float], b: dict[str, float]) -> float:
        dot = sum(a[t] * b.get(t, 0.0) for t in a)
        na = _math.sqrt(sum(v * v for v in a.values()))
        nb = _math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    qvec = vec(_tokens(query))
    scored = []
    for n in names:
        s = cosine(qvec, vec(doc_tokens[n]))
        # min_score (standard IR practice): incidental single-term overlap in
        # long docs yields tiny cosine values; real queries score higher.
        if s >= 0.06:
            scored.append((s, registry[n]))
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
_IDEMPOTENCY_MAX = 2000


def _params_hash(params: dict) -> str:
    import hashlib
    import json as _json
    return hashlib.sha256(
        _json.dumps(params or {}, sort_keys=True, default=str).encode()).hexdigest()


def _idem_prune(data: dict) -> None:
    if len(data) > _IDEMPOTENCY_MAX:
        keep = sorted(data.items(),
                      key=lambda kv: kv[1].get("claimed_at", 0))[-_IDEMPOTENCY_MAX:]
        data.clear()
        data.update(keep)


def _idem_reserve(key: str, skill: str, action: str,
                  params_hash: str) -> tuple[bool, dict | None]:
    """Atomically claim an idempotency key — the concurrency-safe core.

    Returns ``(owned, record)``:
    - ``(True, None)`` — we created a PENDING record; we own the execution.
    - ``(True, None)`` — we atomically moved a FAILED record back to
      PENDING; we own the single retry.
    - ``(False, record)`` — the key is already owned (PENDING in-flight or
      SUCCEEDED); the caller must not execute.

    The check and the claim happen inside ONE file-locked critical
    section, so two concurrent processes cannot both start. A key claimed
    for different skill/action/params raises IdempotencyConflict.

    CRASH SEMANTICS (honest; proven in test_v221_idempotency_semantics.py,
    extended by the v2.3 write-ahead log in skillhub/wal.py):
    - success → SUCCEEDED; replays return the stored result, the handler
      never re-runs for the same key+call.
    - SkillError / unexpected exception / output-contract violation →
      FAILED; the documented retry path may claim it again.
    - hard crash (SIGKILL, power loss) between reserve and commit → the
      key stays PENDING. The WAL phase history + owner-PID liveness let
      ``idempotency_recover`` classify it: crashed *before* any external
      call (no ``side_effect_started`` record, owner dead) → provably safe
      to reclaim as FAILED (one retry allowed); crashed *during/after*
      the call → ``needs_reconciliation`` (human decides, never
      auto-retried); owner still alive or liveness unknown → in-flight,
      untouched. Without the WAL (or when it is unreadable) every stale
      key stays a manual mystery, as in v2.2.
    - crash after a provider side effect but before _idem_commit is NOT
      solved by this local runtime: a retried execution may repeat the
      side effect. The WAL converts the silent ambiguity into an explicit
      ``needs_reconciliation`` report. Providers with their own
      idempotency keys are the real fix (see the threat model).
    """
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as data:
        existing = data.get(key)
        if existing:
            if (existing.get("skill"), existing.get("action"),
                    existing.get("params_hash")) != (skill, action, params_hash):
                raise IdempotencyConflict(
                    f"Idempotency key '{key}' was already used for a "
                    f"different call.")
            if existing.get("status") == "failed":
                existing["status"] = "pending"
                existing["claimed_at"] = int(time.time())
                existing["error_code"] = None
                existing["owner_pid"] = os.getpid()
                existing["owner_token"] = wal.owner_token()
                return True, None
            return False, dict(existing)
        data[key] = {"skill": skill, "action": action,
                     "params_hash": params_hash, "status": "pending",
                     "result": None, "error_code": None,
                     "claimed_at": int(time.time()),
                     "owner_pid": os.getpid(),
                     "owner_token": wal.owner_token()}
        _idem_prune(data)
        return True, None


def _idem_commit(key: str, result: Any) -> None:
    """Atomically mark a claimed key SUCCEEDED with its result.

    The stored result is a JSON-round-tripped snapshot: exotic Python
    values (``datetime``, ``set``, ...) are coerced with ``str()`` so the
    store write can never crash on a handler's return type. The caller
    keeps the original object; replays return the JSON snapshot.
    """
    raw = result if isinstance(result, dict) else {"result": result}
    snapshot = json.loads(json.dumps(raw, ensure_ascii=False, default=str))
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as data:
        rec = data.get(key)
        if rec:
            rec["status"] = "succeeded"
            rec["result"] = snapshot
            rec["completed_at"] = int(time.time())


def _idem_fail(key: str, error_code: str) -> None:
    """Atomically mark a claimed key FAILED (exactly one retry allowed later)."""
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as data:
        rec = data.get(key)
        if rec:
            rec["status"] = "failed"
            rec["error_code"] = error_code


def _idem_release(key: str, actor: str = "local-user") -> bool:
    """Operator escape hatch: delete an idempotency key record entirely.

    Use ONLY after verifying no execution is running for this key (e.g. a
    crashed process left it PENDING). The release is audit-logged. Returns
    True when a record existed and was removed.
    """
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as data:
        if key not in data:
            return False
        rec = data.pop(key)
    audit.log({
        "skill": "runtime", "action": "idempotency_release", "result": "success",
        "actor": actor, "params_hash": "sha256:manual",
        "params_preview": {"idempotency_key": key,
                           "released_status": rec.get("status")},
        "risk": "write",
    })
    return True


def _idem_list() -> list[dict]:
    """Operator introspection: all idempotency records newest-first."""
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as data:
        rows = [{"idempotency_key": k, **v} for k, v in data.items()]
    rows.sort(key=lambda r: r.get("claimed_at", 0), reverse=True)
    return rows


def idempotency_recover(*, apply: bool = True,
                        actor: str = "local-user") -> dict:
    """Classify stale PENDING idempotency keys via the write-ahead log.

    For every PENDING key, ``wal.classify`` decides:

    - ``safe_to_reclaim`` — owner dead, handler provably never ran. With
      ``apply=True`` the record moves to FAILED with error_code
      ``recovered_crash_before_side_effect`` (audit-logged), which re-arms
      the normal one-retry path. Provably safe: the
      ``side_effect_started`` WAL record is fsync'd *before* the handler
      is invoked, so its absence proves no external call happened.
    - ``needs_reconciliation`` — owner dead during/after the call, or the
      WAL is unreadable. Reported with skill/action/timestamps for a
      human. NEVER auto-touched: a retry could repeat the side effect.
    - ``in_flight`` — owner alive, or liveness inconclusive. Untouched.
    - non-PENDING — counted as settled, untouched.

    With ``apply=False`` this is a dry run: nothing is mutated and the
    WAL is not pruned. Returns a report dict.
    """
    report: dict = {"reclaimed": [], "needs_reconciliation": [],
                    "in_flight": [], "settled": 0, "dry_run": not apply}
    data = localstore.read_json(_IDEMPOTENCY_STORE, {})
    pending = [(k, dict(v)) for k, v in data.items()
               if isinstance(v, dict) and v.get("status") == "pending"]
    report["settled"] = len(data) - len(pending)
    verdicts = [(k, rec, wal.classify(k, rec)) for k, rec in pending]
    if not apply:
        for k, rec, verdict in verdicts:
            bucket = {"safe_to_reclaim": "reclaimed",
                      "needs_reconciliation": "needs_reconciliation"}.get(
                          verdict, "in_flight")
            if bucket == "needs_reconciliation":
                report[bucket].append(_reconcile_info(k, rec))
            else:
                report[bucket].append(k)
        return report
    with localstore.locked_json(_IDEMPOTENCY_STORE, {}) as store:
        for key, rec, verdict in verdicts:
            cur = store.get(key)
            if not isinstance(cur, dict) or cur.get("status") != "pending":
                continue  # settled or released while we classified; skip
            if verdict == wal.SAFE_TO_RECLAIM:
                # Re-verify liveness under the lock: never reclaim a key
                # whose owner might have come back.
                if wal.pid_alive(cur.get("owner_pid")) is not False:
                    report["in_flight"].append(key)
                    continue
                cur["status"] = "failed"
                cur["error_code"] = "recovered_crash_before_side_effect"
                cur["recovered_at"] = int(time.time())
                cur["recovered_by"] = actor
                report["reclaimed"].append(key)
                audit.log({
                    "skill": "runtime", "action": "idempotency_recover",
                    "result": "success", "actor": actor,
                    "params_hash": "sha256:manual",
                    "params_preview": {
                        "idempotency_key": key,
                        "verdict": wal.SAFE_TO_RECLAIM,
                        "previous_owner_pid": cur.get("owner_pid"),
                    },
                    "risk": "write",
                })
            elif verdict == wal.NEEDS_RECONCILIATION:
                report["needs_reconciliation"].append(_reconcile_info(key, cur))
            else:
                report["in_flight"].append(key)
    wal.prune()
    return report


def _reconcile_info(key: str, rec: dict) -> dict:
    """Human-readable summary of a key that needs manual reconciliation."""
    phases = wal.phases_for(key)
    return {
        "idempotency_key": key,
        "skill": rec.get("skill"),
        "action": rec.get("action"),
        "claimed_at": rec.get("claimed_at"),
        "owner_pid": rec.get("owner_pid"),
        "wal_phases": phases,
        "hint": ("The owner died after the external call may have run. "
                 "Check the provider's state for this action, then either "
                 f"release the key (skillhub idempotency release {key}) "
                 "if the call never happened, or reconcile manually."),
    }


def _missing_env(entry: SkillEntry) -> list[str]:
    from . import credentials as creds
    return [v for v in entry.required_env if not creds.has(v)]


async def dispatch(entry: SkillEntry, action: str, params: dict,
                   confirm: bool = False, *,
                   approval_id: str | None = None,
                   idempotency_key: str | None = None,
                   request_id: str | None = None,
                   actor: str = "local-user",
                   policy: PolicyEngine | None = None) -> dict:
    """Execute one skill action through the v2.1 pipeline.

    params → validate → policy → approval → credentials → scope check
           → idempotency reserve → handler → output validation
           → idempotency commit → audit

    Reservation happens BEFORE the handler runs (never after): a retry
    that arrives while the first execution is in-flight sees PENDING and
    is rejected instead of double-executing. Approval is consumed before
    any key is claimed, so failed approvals never pollute the idempotency
    store with dead PENDING keys.
    """
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

        # 1. input validation — before anything else (schema is source of truth)
        validate_params(entry.name, action, action_def.parameters,
                        action_def.required, params, strict=action_def.strict)

        # 2. policy
        risk = risk_for(entry.name, action, action_def.risk)
        verdict = policy.evaluate(entry.name, action, risk)
        if verdict == "deny":
            raise PolicyBlocked(entry.name, action,
                                f"policy rule denies {entry.name}.{action}")

        # 3. approval for anything riskier than read (actor-bound, atomic)
        approval_used = ""
        if verdict == "approval_required":
            if approval_id:
                approval.consume(approval_id, entry.name, action, params,
                                 risk, actor=actor)
                approval_used = approval_id
            elif confirm and risk == "write":
                pass  # legacy simple confirmation for plain writes
            else:
                pending = approval.request_approval(
                    entry.name, action, params, risk=risk, actor=actor,
                    preview={k: params.get(k) for k in action_def.required},
                    extra_secret_keys=tuple(action_def.sensitive_params))
                raise ApprovalRequired(entry.name, action,
                                       preview=pending["preview"],
                                       approval_id=pending["approval_id"])

        # 4. credentials must exist before anything is claimed or executed
        missing = _missing_env(entry)
        if missing:
            from .errors import CredentialsMissing
            raise CredentialsMissing(entry.name, missing, entry.setup_help)

        # 5. credential scope check — GATE 1: resolve ONCE per credential
        #    and verify scopes on that SAME CredentialResolution object.
        #    Never check scopes on a same-named record from another source.
        from . import credentials as creds
        resolutions = [creds.resolve_credential(name, entry.name)
                       for name in entry.required_env]
        credential_source = ",".join(
            f"{r.name}:{r.source}" for r in resolutions)
        scope_check = ""
        if action_def.required_scopes:
            checks = [creds.require_scopes(r, action_def.required_scopes,
                                           entry.name)
                      for r in resolutions]
            scope_check = ("verified" if all(c == "verified" for c in checks)
                           else "unverified")

        # 6. idempotency reservation — atomic claim BEFORE the handler runs
        reserved = False
        if risk != "read" and action_def.supports_idempotency_key and idempotency_key:
            owned, existing = _idem_reserve(
                idempotency_key, entry.name, action, _params_hash(params))
            if not owned:
                assert existing is not None
                if existing.get("status") == "succeeded":
                    result = dict(existing.get("result") or {})
                    result["deduplicated"] = True
                    _audit("deduplicated", risk=risk, approval_id=approval_used,
                           idempotency_key=idempotency_key,
                           scope_check=scope_check,
                           credential_source=credential_source)
                    return result
                # pending → another execution owns this key right now.
                # (If that execution crashed, the key stays PENDING: run
                # `skillhub idempotency recover` to classify it via the
                # write-ahead log — provably-safe crashes are reclaimed
                # automatically, the rest are reported for a human. An
                # operator may also release the key manually after verifying
                # nothing is running: `skillhub idempotency release <key>`.)
                raise IdempotencyConflict(
                    f"Idempotency key '{idempotency_key}' is already claimed "
                    f"by an in-flight execution; retry after it completes. "
                    f"If the holder crashed, classify it with: skillhub "
                    f"idempotency recover (or release it manually with: "
                    f"skillhub idempotency release {idempotency_key})")
            reserved = True
            # WAL intent: durably record that we own this key BEFORE any
            # external call. side_effect_started (below) is the proof
            # boundary — its absence proves the handler never ran.
            wal.record(idempotency_key, wal.INTENT, skill=entry.name,
                       action=action, params_hash=_params_hash(params))

        # 7. execute — the WAL brackets the handler so crash recovery can
        # tell "died before the provider call" from "died after it".
        try:
            if reserved:
                wal.record(idempotency_key, wal.SIDE_EFFECT_STARTED,
                           skill=entry.name, action=action,
                           params_hash=_params_hash(params))
            result = await action_def.handler(dict(params))
            if reserved:
                wal.record(idempotency_key, wal.SIDE_EFFECT_DONE,
                           skill=entry.name, action=action,
                           params_hash=_params_hash(params))
        except SkillError as exc:
            if reserved:
                _idem_fail(idempotency_key, exc.code)
            raise
        except Exception as exc:  # never leak tracebacks as success
            if reserved:
                _idem_fail(idempotency_key, "upstream_error")
            raise UpstreamError(entry.name, f"{type(exc).__name__}: {exc}",
                                action=action) from exc

        # 8. output validation — the declared contract is enforced, not documented
        try:
            result = validate_output(entry.name, action,
                                     action_def.output_schema, result)
        except SkillError as exc:
            if reserved:
                _idem_fail(idempotency_key, exc.code)
            raise

        # 9. commit the idempotency record atomically
        if reserved:
            _idem_commit(idempotency_key, result)

        _audit("success", risk=risk, approval_id=approval_used,
               idempotency_key=idempotency_key or "",
               scope_check=scope_check, credential_source=credential_source)
        if isinstance(result, dict):
            result = dict(result)
            result.setdefault("meta", {})["request_id"] = request_id
            return result
        return {"status": "ok", "result": result,
                "meta": {"request_id": request_id}}
    except SkillError as exc:
        _audit("error", risk=locals().get("risk", ""),
               error_code=exc.code,
               # internal is debug detail (it may echo provider bodies) —
               # scrub secret-shaped substrings before it reaches the log
               error_internal=audit.scrub_text(exc.internal)
               if exc.internal else "")
        raise

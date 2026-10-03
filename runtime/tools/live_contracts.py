#!/usr/bin/env python3
"""Live contract-test runner (v2.3).

Runs REAL driver code against LIVE provider APIs — read-only smoke calls.
This is step 2 of the provider contract matrix (step 1 was the mock
harness in tests/test_provider_contracts.py).

Tiers:
  public — no credential needed; runs anywhere (e.g. podcast/iTunes).
  keyed  — needs provider API key from env; SKIP with the exact key
           name when absent. The report doubles as the key checklist.
  local  — local/stateful drivers (no HTTP); excluded, covered by the
           unit suite.

Safety: only ``risk == "read"`` actions are ever executed; anything
else is refused. Every run uses an isolated SKILLHUB_LOCAL_DIR unless
``--keep-data`` is passed, so live smoke calls never pollute the real
audit/idempotency stores.

Usage:
  python tools/live_contracts.py [--only SKILL] [--dry-run]
                                 [--report PATH] [--keep-data]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skillhub import registry  # noqa: E402

# --- curated specs: (skill, action, params, env_vars, tier, expect_key) ------
# expect_key: result[expect_key] must exist (None → generic "dict, no error").
CURATED = [
    ("podcast", "search_podcasts", {"query": "python", "limit": 1},
     [], "public", "podcasts"),
    ("ticketmaster", "search_events", {"keyword": "jazz", "size": 1},
     ["TICKETMASTER_API_KEY"], "keyed", "events"),
    ("github", "search_repositories", {"query": "mcp", "per_page": 1},
     ["GITHUB_TOKEN"], "keyed", "repositories"),
    ("stripe", "list_customers", {"limit": 1},
     ["STRIPE_SECRET_KEY"], "keyed", "customers"),
    ("lovable", "list_workspaces", {},
     ["LOVABLE_API_KEY"], "keyed", "workspaces"),
    ("replit", "list_workspaces", {},
     ["REPLIT_API_KEY"], "keyed", "workspaces"),
    ("granola", "list_notes", {"page_size": 1},
     ["GRANOLA_API_KEY"], "keyed", "notes"),
    ("flightaware", "flight_status", {"ident": "GAE856"},
     ["FLIGHTAWARE_API_KEY"], "keyed", None),
]

LOCAL_HINTS = ("localstore", "device", "vault", "library", "healthkit",
               "wearable", "paired", "connector-management", "permission-model",
               "idea-management", "share-ideas", "skill-creator",
               "agent-library", "muse-feedback", "self-awareness",
               "function-health", "data-control", "forget", "goals",
               "personal-feed", "messaging-channels", "secure-vault",
               "subscription-status", "wallet", "apple-healthkit",
               "google-health-connect", "media-library", "magic-moment",
               "travel-planning", "booking", "opentable", "generate_podcast")


def _uses_http(skill: str) -> bool:
    """True when the driver module performs HTTP (vs local/stateful)."""
    base = Path(__file__).resolve().parent.parent / "skillhub" / "skills"
    for cand in (f"{skill}.py", f"{skill.replace('-', '_')}.py"):
        p = base / cand
        if p.exists():
            src = p.read_text(encoding="utf-8")
            return "api_request(" in src or "raw_request(" in src
    return False


def build_specs() -> list[dict]:
    """Curated specs + auto-derived keyed entries for every HTTP driver."""
    reg = registry.load_registry()
    specs: list[dict] = []
    curated_skills = set()
    for skill, action, params, env, tier, expect in CURATED:
        entry = reg.get(skill)
        if entry is None or not entry.implemented:
            continue
        curated_skills.add(skill)
        specs.append({"skill": skill, "action": action, "params": params,
                      "env": env, "tier": tier, "expect": expect,
                      "origin": "curated"})
    for name, entry in sorted(reg.items()):
        if not entry.implemented or name in curated_skills:
            continue
        if not _uses_http(name):
            continue  # local/stateful — unit suite covers it
        reads = [(a, d) for a, d in entry.actions.items()
                 if d.risk == "read"]
        if not reads:
            specs.append({"skill": name, "action": None, "params": {},
                          "env": entry.required_env, "tier": "keyed",
                          "expect": None, "origin": "auto",
                          "note": "no read action — needs manual spec"})
            continue
        noarg = next((a for a, d in reads if not d.required), None)
        action = noarg or reads[0][0]
        specs.append({
            "skill": name, "action": action,
            "params": {} if noarg else {"__NEEDS_PARAMS__": True},
            "env": entry.required_env, "tier": "keyed", "expect": None,
            "origin": "auto",
            **({} if noarg else {"note": "read action needs params — manual spec"}),
        })
    return specs


async def _run_one(reg, spec: dict) -> dict:
    skill, action = spec["skill"], spec["action"]
    if action is None or spec["params"].get("__NEEDS_PARAMS__"):
        return {"skill": skill, "status": "SKIP",
                "reason": spec.get("note", "no runnable spec")}
    missing = [v for v in spec["env"] if not os.environ.get(v)]
    if missing:
        return {"skill": skill, "status": "SKIP",
                "reason": f"needs {', '.join(missing)}"}
    entry = reg[skill]
    action_def = entry.actions.get(action)
    if action_def is None or action_def.risk != "read":
        return {"skill": skill, "status": "SKIP",
                "reason": "refused: not a read action"}
    t0 = time.monotonic()
    try:
        result = await asyncio.wait_for(
            registry.dispatch(entry, action, dict(spec["params"]),
                              confirm=False),
            timeout=60)
    except Exception as exc:  # noqa: BLE001 — report, don't crash the matrix
        code = getattr(exc, "code", type(exc).__name__)
        return {"skill": skill, "status": "FAIL",
                "reason": f"{code}: {str(exc)[:160]}",
                "duration_ms": int((time.monotonic() - t0) * 1000)}
    duration_ms = int((time.monotonic() - t0) * 1000)
    if not isinstance(result, dict):
        return {"skill": skill, "status": "FAIL",
                "reason": f"unexpected result type {type(result).__name__}",
                "duration_ms": duration_ms}
    expect = spec["expect"]
    if expect and expect not in result:
        return {"skill": skill, "status": "FAIL",
                "reason": f"result missing key '{expect}'",
                "duration_ms": duration_ms}
    return {"skill": skill, "status": "PASS", "action": action,
            "tier": spec["tier"], "duration_ms": duration_ms}


async def _amain(specs: list[dict], only: str | None) -> list[dict]:
    reg = registry.load_registry()
    results = []
    for spec in specs:
        if only and spec["skill"] != only:
            continue
        results.append(await _run_one(reg, spec))
    return results


def _markdown(results: list[dict]) -> str:
    lines = ["# Live contract-test report",
             "",
             f"_Generated {time.strftime('%Y-%m-%d %H:%M %Z')}. "
             "Read-only smoke calls against live provider APIs._",
             "",
             "| Skill | Action | Tier | Status | Detail |",
             "|---|---|---|---|---|"]
    for r in results:
        detail = r.get("reason") or f"{r.get('duration_ms', 0)} ms"
        lines.append(f"| {r['skill']} | {r.get('action', '—')} "
                     f"| {r.get('tier', '—')} | **{r['status']}** | {detail} |")
    passes = sum(1 for r in results if r["status"] == "PASS")
    skips = [r for r in results if r["status"] == "SKIP"]
    fails = sum(1 for r in results if r["status"] == "FAIL")
    lines += ["",
              f"**{passes} PASS · {len(skips)} SKIP · {fails} FAIL** "
              f"out of {len(results)}.",
              "",
              "## Keys needed (one per SKIP)",
              ""]
    need = sorted({r["reason"].replace("needs ", "")
                   for r in skips if r["reason"].startswith("needs ")})
    for n in need:
        lines.append(f"- `{n}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="run a single skill")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the matrix without calling anything")
    ap.add_argument("--report", default="visibility/live-contracts-report.md",
                    help="where to write the markdown report")
    ap.add_argument("--keep-data", action="store_true",
                    help="use the real SKILLHUB_LOCAL_DIR (default: isolated tmp)")
    args = ap.parse_args()

    if not args.keep_data:
        os.environ["SKILLHUB_LOCAL_DIR"] = tempfile.mkdtemp(
            prefix="skillhub-live-")
    specs = build_specs()
    if args.only:
        specs = [s for s in specs if s["skill"] == args.only]
        if not specs:
            print(f"unknown skill: {args.only}")
            return 2
    if args.dry_run:
        for s in specs:
            env = ",".join(s["env"]) or "none"
            print(f"{s['skill']:28} {str(s['action']):24} "
                  f"{s['tier']:7} env={env} [{s['origin']}]")
        print(f"\n{len(specs)} specs (dry run)")
        return 0
    results = asyncio.run(_amain(specs, args.only))
    for r in results:
        detail = r.get("reason") or f"{r.get('duration_ms', 0)}ms"
        print(f"[{r['status']:4}] {r['skill']:28} {detail}")
    passes = sum(1 for r in results if r["status"] == "PASS")
    fails = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{passes} PASS, {len(results) - passes - fails} SKIP, {fails} FAIL")
    repo_root = Path(__file__).resolve().parent.parent.parent
    out = repo_root / args.report
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_markdown(results), encoding="utf-8")
    print(f"report → {out}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

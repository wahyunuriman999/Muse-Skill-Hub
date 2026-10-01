"""Function health — runtime self health check.

Reports the health of this skill runtime: registry load, driver coverage,
dependency versions, and local-store writability. (The Function Health *lab
results* product has no public API; this driver checks the runtime itself.)
"""
from __future__ import annotations

from ..driver import ActionDef
from ..localstore import data_dir

SKILL = "function-health"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "No setup needed — checks the running runtime."


async def runtime_health(params: dict) -> dict:
    from ..registry import load_registry
    checks = {}
    try:
        reg = load_registry()
        checks["registry"] = {"ok": True, "skills": len(reg),
                              "executable": sum(1 for e in reg.values() if e.implemented)}
    except Exception as exc:
        checks["registry"] = {"ok": False, "error": str(exc)}
    for dep in ("httpx", "mcp"):
        try:
            mod = __import__(dep)
            checks[dep] = {"ok": True,
                           "version": getattr(mod, "__version__", "unknown")}
        except Exception as exc:
            checks[dep] = {"ok": False, "error": str(exc)}
    try:
        d = data_dir()
        probe = d / ".health-probe"
        probe.write_text("ok")
        probe.unlink()
        checks["local_store"] = {"ok": True, "path": str(d)}
    except Exception as exc:
        checks["local_store"] = {"ok": False, "error": str(exc)}
    healthy = all(c.get("ok") for c in checks.values())
    return {"status": "ok", "healthy": healthy, "checks": checks}


async def query_audit_log(params: dict) -> dict:
    from .. import audit
    rows = audit.query(limit=int(params.get("limit", 50)),
                       skill=params.get("skill", ""),
                       action=params.get("action", ""),
                       result=params.get("result", ""))
    return {"status": "ok", "events": rows, "count": len(rows)}


ACTIONS = {
    "runtime_health": ActionDef("Run the runtime self health check.",
        {}, [], runtime_health),
    "query_audit_log": ActionDef(
        "Query the runtime audit log (newest first). Secrets are never stored raw.",
        {"limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
         "skill": {"type": "string", "default": ""},
         "action": {"type": "string", "default": ""},
         "result": {"type": "string",
                    "enum": ["", "success", "error", "blocked", "deduplicated"],
                    "default": ""}},
        [], query_audit_log),
}

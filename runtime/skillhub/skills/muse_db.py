"""muse_db — LOCAL SQLite inspection store (guardrailed).

A real local SQLite database for diagnosis-style record keeping. This is a
local reference implementation — it does not reach any production database.
Set SKILLHUB_DB_PATH to override the default (~/.skillhub-local/muse.db).

Guardrails (issue: arbitrary SQL is too powerful a primitive):
- single statement only (no stacked queries)
- query: SELECT/WITH only, 200-row cap, 5s timeout
- execute_write: INSERT/UPDATE/DELETE only — DROP/ALTER/ATTACH/PRAGMA/
  VACUUM/CREATE TRIGGER etc. are rejected
- write needs approval (risk=destructive) and is audit-logged by the runtime
"""
from __future__ import annotations

import os
import sqlite3

from ..driver import ActionDef
from ..errors import SkillError
from ..localstore import data_dir

SKILL = "muse_db"
REQUIRED_ENV: list[str] = []
SETUP_HELP = ("No setup needed — local SQLite file. "
              "Set SKILLHUB_DB_PATH to use a different file.")

_READ_PREFIXES = ("select", "with")
# CREATE TABLE/INDEX allowed: this is a local scratch DB and the driver's
# purpose includes creating tables. DROP/ALTER/ATTACH/PRAGMA stay blocked.
_WRITE_PREFIXES = ("insert", "update", "delete", "create table", "create index")
_BLOCKED_KEYWORDS = ("attach", "detach", "pragma", "vacuum", "reindex",
                     "drop ", "drop\t", "drop\n", "alter ", "create trigger",
                     "load_extension")
_ROW_CAP = 200


def _db() -> sqlite3.Connection:
    path = os.environ.get("SKILLHUB_DB_PATH", str(data_dir() / "muse.db"))
    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def _single_statement(sql: str) -> str:
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise SkillError("SQL is empty.", code="invalid_input", skill=SKILL)
    # reject stacked statements (naive but effective: semicolons outside quotes)
    depth, in_str, quote = 0, False, ""
    for i, ch in enumerate(sql):
        if in_str:
            if ch == quote and sql[i - 1] != "\\":
                in_str = False
        elif ch in ("'", '"'):
            in_str, quote = True, ch
        elif ch == ";":
            raise SkillError("Only one SQL statement per call.",
                             code="invalid_input", skill=SKILL)
    lowered = sql.lower()
    for kw in _BLOCKED_KEYWORDS:
        if kw in lowered:
            raise SkillError(f"Blocked SQL keyword: '{kw.strip()}'.",
                             code="policy_blocked", skill=SKILL)
    return sql


async def list_tables(params: dict) -> dict:
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return {"status": "ok", "tables": [r["name"] for r in rows]}
    finally:
        conn.close()


async def query(params: dict) -> dict:
    sql = _single_statement(params["sql"])
    if not sql.lower().startswith(_READ_PREFIXES):
        raise SkillError("query only allows SELECT/WITH; use execute_write for writes.",
                         code="invalid_input", skill=SKILL)
    conn = _db()
    try:
        rows = conn.execute(sql).fetchall()
        return {"status": "ok", "rows": [dict(r) for r in rows[:_ROW_CAP]],
                "truncated": len(rows) > _ROW_CAP}
    finally:
        conn.close()


async def execute_write(params: dict) -> dict:
    sql = _single_statement(params["sql"])
    if not sql.lower().startswith(_WRITE_PREFIXES):
        raise SkillError("execute_write allows INSERT/UPDATE/DELETE/CREATE TABLE only.",
                         code="invalid_input", skill=SKILL)
    conn = _db()
    try:
        cur = conn.execute(sql)
        conn.commit()
        return {"status": "ok", "rows_affected": cur.rowcount}
    finally:
        conn.close()


ACTIONS = {
    "list_tables": ActionDef("List tables in the local database.", {}, [], list_tables,
        output_schema={"type": "object"}),
    "query": ActionDef("Run a read-only SELECT/WITH query (200-row cap).",
        {"sql": {"type": "string", "maxLength": 8000}}, ["sql"], query,
        output_schema={"type": "object"}),
    "execute_write": ActionDef("Run INSERT/UPDATE/DELETE (needs approval; DROP/ALTER/PRAGMA blocked).",
        {"sql": {"type": "string", "maxLength": 8000}}, ["sql"], execute_write,
        write=True, risk="destructive", output_schema={"type": "object"}),
}

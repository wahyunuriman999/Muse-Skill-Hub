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
_BLOCKED_KEYWORDS = ("attach", "detach", "pragma", "vacuum", "reindex",
                     "drop ", "drop\t", "drop\n", "alter ", "create trigger",
                     "load_extension")
_ROW_CAP = 200


def _strip_comments_and_strings(sql: str) -> str:
    """Remove -- comments, /* */ comments, and string literals.

    Keyword scanning runs on the result, so `DROP` hidden inside a
    comment or a string literal can neither bypass the blocklist nor
    trigger a false positive.
    """
    out = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if ch == "'" or ch == '"':
            # skip string literal ('' is an escaped quote in SQL)
            i += 1
            while i < n:
                if sql[i] == ch:
                    if i + 1 < n and sql[i + 1] == ch:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append(" ")
        elif ch == "-" and nxt == "-":
            while i < n and sql[i] != "\n":
                i += 1
        elif ch == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _db(readonly: bool = False) -> sqlite3.Connection:
    path = os.environ.get("SKILLHUB_DB_PATH", str(data_dir() / "muse.db"))
    if readonly:
        # mode=ro cannot create the file — ensure it exists first (empty DB,
        # no user data written), then reopen read-only.
        if not os.path.exists(path):
            sqlite3.connect(path, timeout=5.0).close()
        # Defense in depth: the OS-level connection itself cannot write,
        # even if the lexical guardrails below ever missed something.
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5.0)
    else:
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
    # scan the comment/string-stripped form: keywords hidden in comments or
    # string literals are not executable SQL, and executable keywords cannot
    # hide inside them.
    stripped = _strip_comments_and_strings(lowered)
    for kw in _BLOCKED_KEYWORDS:
        if kw in stripped:
            raise SkillError(f"Blocked SQL keyword: '{kw.strip()}'.",
                             code="policy_blocked", skill=SKILL)
    # the statement must actually START with the claimed operation after
    # stripping leading comments
    first_token = stripped.lstrip().split(None, 1)[0] if stripped.strip() else ""
    return sql, first_token


async def list_tables(params: dict) -> dict:
    conn = _db(readonly=True)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return {"status": "ok", "tables": [r["name"] for r in rows]}
    finally:
        conn.close()


async def query(params: dict) -> dict:
    sql, first = _single_statement(params["sql"])
    if first not in _READ_PREFIXES:
        raise SkillError("query only allows SELECT/WITH; use execute_write for writes.",
                         code="invalid_input", skill=SKILL)
    conn = _db(readonly=True)
    try:
        rows = conn.execute(sql).fetchall()
        return {"status": "ok", "rows": [dict(r) for r in rows[:_ROW_CAP]],
                "truncated": len(rows) > _ROW_CAP}
    finally:
        conn.close()


async def execute_write(params: dict) -> dict:
    sql, first = _single_statement(params["sql"])
    if not any(first == p or first.startswith(p) for p in ("insert", "update", "delete")) \
            and first not in ("create",):
        raise SkillError("execute_write allows INSERT/UPDATE/DELETE/CREATE TABLE only.",
                         code="invalid_input", skill=SKILL)
    if first == "create" and not _strip_comments_and_strings(sql.lower()).lstrip().startswith(
            ("create table", "create index")):
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

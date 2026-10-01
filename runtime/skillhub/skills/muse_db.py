"""muse_db — LOCAL SQLite inspection store.

A real local SQLite database for diagnosis-style record keeping: create tables,
run read queries, and trace records. This is a local reference implementation —
it does not reach any production database. Set SKILLHUB_DB_PATH to override the
default (~/.skillhub-local/muse.db).
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


def _db() -> sqlite3.Connection:
    path = os.environ.get("SKILLHUB_DB_PATH", str(data_dir() / "muse.db"))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


async def list_tables(params: dict) -> dict:
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return {"status": "ok", "tables": [r["name"] for r in rows]}
    finally:
        conn.close()


async def query(params: dict) -> dict:
    sql = params["sql"].strip()
    if not sql.lower().startswith("select"):
        raise SkillError(SKILL, "read_only",
                         "query only allows SELECT; use execute_write for writes.")
    conn = _db()
    try:
        rows = conn.execute(sql).fetchall()
        return {"status": "ok", "rows": [dict(r) for r in rows[:200]],
                "truncated": len(rows) > 200}
    finally:
        conn.close()


async def execute_write(params: dict) -> dict:
    conn = _db()
    try:
        cur = conn.execute(params["sql"])
        conn.commit()
        return {"status": "ok", "rows_affected": cur.rowcount}
    finally:
        conn.close()


ACTIONS = {
    "list_tables": ActionDef("List tables in the local database.", {}, [], list_tables),
    "query": ActionDef("Run a read-only SELECT query.",
        {"sql": {"type": "string"}}, ["sql"], query),
    "execute_write": ActionDef("Run a write statement (needs confirm=true).",
        {"sql": {"type": "string"}}, ["sql"], execute_write, write=True),
}

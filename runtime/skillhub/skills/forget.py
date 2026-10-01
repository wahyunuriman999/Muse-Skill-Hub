"""Forget — LOCAL memory-fact removal reference implementation.

Removes matching facts from the runtime's local memory store. Reference
implementation of the forget interface — production memory systems should also
purge derived copies and scheduled producers of the forgotten fact.
"""
from __future__ import annotations

from ..driver import ActionDef
from ..localstore import LOCAL_NOTE, read_json, write_json

SKILL = "forget"
REQUIRED_ENV: list[str] = []
SETUP_HELP = LOCAL_NOTE

_STORE = "memory-facts"


async def remember_fact(params: dict) -> dict:
    facts = read_json(_STORE, [])
    facts.append({"fact": params["fact"], "topic": params.get("topic", "")})
    write_json(_STORE, facts)
    return {"status": "ok", "remembered": params["fact"][:80]}


async def list_facts(params: dict) -> dict:
    return {"status": "ok", "facts": read_json(_STORE, [])}


async def forget_fact(params: dict) -> dict:
    q = params["query"].lower()
    facts = read_json(_STORE, [])
    kept = [f for f in facts if q not in f.get("fact", "").lower()
            and q not in f.get("topic", "").lower()]
    removed = len(facts) - len(kept)
    write_json(_STORE, kept)
    return {"status": "ok", "removed": removed,
            "note": "Also purge any derived copies or scheduled jobs reproducing this fact."}


ACTIONS = {
    "remember_fact": ActionDef("Store a fact in local memory (needs confirm=true).",
        {"fact": {"type": "string"}, "topic": {"type": "string"}},
        ["fact"], remember_fact, write=True),
    "list_facts": ActionDef("List stored facts.", {}, [], list_facts),
    "forget_fact": ActionDef("Remove facts matching a query (needs confirm=true).",
        {"query": {"type": "string"}}, ["query"], forget_fact, write=True),
}

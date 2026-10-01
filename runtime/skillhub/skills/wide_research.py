"""Wide research driver — real multi-query web research via Serper.dev.

Runs several focused searches for one research question and returns the
combined, deduplicated sources — the retrieval half of deep research.
Set SERPER_API_KEY (shared with image-search/shopping).
"""
from __future__ import annotations

import asyncio
import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "wide-research"
REQUIRED_ENV = ["SERPER_API_KEY"]
SETUP_HELP = (
    "Sign up at https://serper.dev, copy your API key, and set SERPER_API_KEY."
)

_BASE = "https://google.serper.dev/search"


def _headers() -> dict:
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"X-API-KEY": key, "Content-Type": "application/json"}


async def _one(query: str, num: int) -> list[dict]:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"q": query, "num": num})
    out = []
    for x in r.get("organic", []):
        out.append({"title": x.get("title"), "link": x.get("link"),
                    "snippet": x.get("snippet")})
    return out


async def research(params: dict) -> dict:
    queries = params.get("queries") or [params["question"]]
    per = max(3, min(int(params.get("results_per_query", 5)), 10))
    results = await asyncio.gather(*[_one(q, per) for q in queries[:5]])
    seen, merged = set(), []
    for batch in results:
        for item in batch:
            if item["link"] and item["link"] not in seen:
                seen.add(item["link"])
                merged.append(item)
    return {"status": "ok", "question": params.get("question"),
            "queries_run": queries[:5], "sources": merged}


ACTIONS = {
    "research": ActionDef("Run parallel web searches for a research question.",
        {"question": {"type": "string"},
         "queries": {"type": "array", "items": {"type": "string"},
                     "description": "Up to 5 focused sub-queries (defaults to [question])"},
         "results_per_query": {"type": "integer", "default": 5, "maximum": 10}},
        ["question"], research),
}

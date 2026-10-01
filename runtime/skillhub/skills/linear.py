"""Linear driver — real Linear GraphQL API implementation.

Setup: Linear > Settings > API > create personal API key. Set LINEAR_API_KEY.
"""
from __future__ import annotations

import os

from ..driver import ActionDef
from ..errors import CredentialsMissing
from ..http import api_request

SKILL = "linear"
REQUIRED_ENV = ["LINEAR_API_KEY"]
SETUP_HELP = "Linear app > Settings > API > Personal API keys > create key."

_BASE = "https://api.linear.app/graphql"


def _headers() -> dict:
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        raise CredentialsMissing(SKILL, REQUIRED_ENV, SETUP_HELP)
    return {"Authorization": key, "Content-Type": "application/json"}


async def _gql(query: str, variables: dict | None = None) -> dict:
    r = await api_request(SKILL, "POST", _BASE, headers=_headers(),
                          json={"query": query, "variables": variables or {}})
    if isinstance(r, dict) and r.get("errors"):
        from ..errors import UpstreamError
        raise UpstreamError(SKILL, str(r["errors"])[:400])
    return r.get("data", {})


async def list_issues(params: dict) -> dict:
    data = await _gql(
        "query($first: Int){ issues(first: $first, orderBy: updatedAt) "
        "{ nodes { id identifier title state { name } priority } } }",
        {"first": min(int(params.get("limit", 10)), 25)})
    return {"status": "ok", "issues": [
        {"id": i["id"], "identifier": i["identifier"], "title": i["title"],
         "state": i["state"]["name"], "priority": i.get("priority")}
        for i in data.get("issues", {}).get("nodes", [])]}


async def create_issue(params: dict) -> dict:
    data = await _gql(
        "mutation($input: IssueCreateInput!){ issueCreate(input: $input) "
        "{ success issue { id identifier title } } }",
        {"input": {"teamId": params["team_id"], "title": params["title"],
                   "description": params.get("description", "")}})
    issue = data.get("issueCreate", {}).get("issue", {})
    return {"status": "ok", "issue": issue}


ACTIONS = {
    "list_issues": ActionDef("List Linear issues.",
        {"limit": {"type": "integer", "default": 10, "maximum": 25}},
        [], list_issues),
    "create_issue": ActionDef("Create a Linear issue (needs confirm=true).",
        {"team_id": {"type": "string", "description": "Linear team UUID"},
         "title": {"type": "string"}, "description": {"type": "string", "default": ""}},
        ["team_id", "title"], create_issue, write=True),
}

"""GitHub driver — real GitHub REST API implementation.

Works without a token for public read endpoints (60 req/hour).
Set GITHUB_TOKEN for higher limits and write actions.
"""
from __future__ import annotations


from ..driver import ActionDef
from ..http import api_request
from ..credentials import maybe_cred

SKILL = "github"
REQUIRED_ENV: list[str] = []
SETUP_HELP = (
    "Optional: set GITHUB_TOKEN (a classic or fine-grained personal access token) "
    "for higher rate limits and write actions such as create_issue."
)

_BASE = "https://api.github.com"


def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = maybe_cred("GITHUB_TOKEN", SKILL)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def search_repositories(params: dict) -> dict:
    data = await api_request(
        SKILL,
        "GET",
        f"{_BASE}/search/repositories",
        headers=_headers(),
        params={
            "q": params["query"],
            "sort": params.get("sort", "best match"),
            "order": params.get("order", "desc"),
            "per_page": min(int(params.get("per_page", 5)), 30),
        },
    )
    items = data.get("items", []) if isinstance(data, dict) else []
    return {
        "status": "ok",
        "total_count": data.get("total_count", 0) if isinstance(data, dict) else 0,
        "repositories": [
            {
                "full_name": r["full_name"],
                "description": r.get("description"),
                "stars": r.get("stargazers_count"),
                "language": r.get("language"),
                "url": r.get("html_url"),
            }
            for r in items
        ],
    }


async def get_repository(params: dict) -> dict:
    r = await api_request(
        SKILL, "GET", f"{_BASE}/repos/{params['owner']}/{params['repo']}", headers=_headers()
    )
    return {
        "status": "ok",
        "repository": {
            "full_name": r["full_name"],
            "description": r.get("description"),
            "stars": r.get("stargazers_count"),
            "forks": r.get("forks_count"),
            "open_issues": r.get("open_issues_count"),
            "language": r.get("language"),
            "default_branch": r.get("default_branch"),
            "url": r.get("html_url"),
        },
    }


async def list_issues(params: dict) -> dict:
    data = await api_request(
        SKILL,
        "GET",
        f"{_BASE}/repos/{params['owner']}/{params['repo']}/issues",
        headers=_headers(),
        params={
            "state": params.get("state", "open"),
            "per_page": min(int(params.get("per_page", 10)), 50),
        },
    )
    items = data if isinstance(data, list) else []
    return {
        "status": "ok",
        "issues": [
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "labels": [l["name"] for l in i.get("labels", [])],
                "url": i.get("html_url"),
            }
            for i in items
        ],
    }


async def create_issue(params: dict) -> dict:
    if not maybe_cred("GITHUB_TOKEN", SKILL):
        from ..errors import CredentialsMissing

        raise CredentialsMissing(
            SKILL,
            ["GITHUB_TOKEN"],
            "Write actions need a token with repo scope.",
        )
    r = await api_request(
        SKILL,
        "POST",
        f"{_BASE}/repos/{params['owner']}/{params['repo']}/issues",
        headers=_headers(),
        json={"title": params["title"], "body": params.get("body", "")},
    )
    return {
        "status": "ok",
        "issue": {"number": r["number"], "title": r["title"], "url": r.get("html_url")},
    }


ACTIONS = {
    "search_repositories": ActionDef(
        description="Search public GitHub repositories by keyword.",
        parameters={
            "query": {"type": "string", "description": "Search keywords, e.g. 'mcp server language:python'"},
            "sort": {"type": "string", "enum": ["best match", "stars", "forks", "updated"], "default": "best match"},
            "per_page": {"type": "integer", "default": 5, "maximum": 30},
        },
        required=["query"],
        handler=search_repositories,
    ),
    "get_repository": ActionDef(
        description="Get details of a public repository.",
        parameters={
            "owner": {"type": "string", "description": "Repository owner"},
            "repo": {"type": "string", "description": "Repository name"},
        },
        required=["owner", "repo"],
        handler=get_repository,
    ),
    "list_issues": ActionDef(
        description="List issues of a repository.",
        parameters={
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
            "per_page": {"type": "integer", "default": 10, "maximum": 50},
        },
        required=["owner", "repo"],
        handler=list_issues,
    ),
    "create_issue": ActionDef(
        description="Create an issue (needs GITHUB_TOKEN + confirm=true).",
        parameters={
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string", "default": ""},
        },
        required=["owner", "repo", "title"],
        handler=create_issue,
        write=True,
    ),
}

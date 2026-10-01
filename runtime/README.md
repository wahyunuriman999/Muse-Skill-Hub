# ⚡ Muse Skill Hub — Executable MCP Runtime

This is the **executable layer** of Muse Skill Hub. It turns the 87-skill catalog
(`skills/*/SKILL.md`) into **real, callable MCP tools** that any MCP-compatible
LLM client (Claude Desktop, etc.) can use plug-and-play.

## How it works

```
skills/*/SKILL.md  ──catalog──▶  skillhub/registry.py  ──▶  MCP server (stdio)
                                           │
                        ┌──────────────────┴──────────────────┐
                        │  11 real API drivers (executable)    │
                        │  76 catalog-only (honest stub)       │
                        └─────────────────────────────────────┘
```

- **Every one of the 87 skills is registered as an MCP tool** — full discovery.
- Skills with a driver in `skillhub/skills/` execute **real API calls**.
- Skills without a driver return a structured `driver_not_implemented` response
  (never a fake success) with a pointer to the driver template.
- **Read/write isolation is enforced in code**: write actions refuse to run
  without `confirm=true`.
- **Credentials are honest**: missing env vars return `credentials_missing`
  with exact setup instructions — no hallucinated data.

## Quick start

```bash
cd runtime
pip install -r requirements.txt

# run the MCP server (stdio transport)
python -m skillhub.server
# → "muse-skill-hub: 87 skills registered, 11 with executable drivers."
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "muse-skill-hub": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "skillhub.server"],
      "cwd": "/path/to/Muse-Skill-Hub/runtime",
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "SLACK_BOT_TOKEN": "xoxb-..."
      }
    }
  }
}
```

## Implemented drivers

| Skill | Actions | Credentials |
|---|---|---|
| `github` | search_repositories, get_repository, list_issues, create_issue | `GITHUB_TOKEN` (optional for reads) |
| `slack` | list_channels, read_channel, send_message | `SLACK_BOT_TOKEN` |
| `stripe` | list_customers, list_invoices, create_payment_link | `STRIPE_SECRET_KEY` |
| `shopify` | list_products, list_orders | `SHOPIFY_STORE`, `SHOPIFY_ADMIN_TOKEN` |
| `linear` | list_issues, create_issue | `LINEAR_API_KEY` |
| `vercel` | list_projects, list_deployments | `VERCEL_TOKEN` |
| `asana` | list_tasks, create_task | `ASANA_ACCESS_TOKEN` |
| `notion` | search, query_database | `NOTION_TOKEN` |
| `todoist` | list_tasks, create_task | `TODOIST_API_TOKEN` |
| `places-search` | search_places | `GOOGLE_MAPS_API_KEY` |
| `zoom` | list_meetings, create_meeting | `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID` |

Each driver module documents its own setup steps in `SETUP_HELP`.

## Calling a tool

Every tool takes `{ action, params, confirm }`:

```json
{ "action": "search_repositories",
  "params": { "query": "mcp server language:python", "per_page": 3 } }
```

Write action (needs confirmation):

```json
{ "action": "send_message",
  "params": { "channel_id": "C012AB345CD", "text": "Hello!" },
  "confirm": true }
```

Without `confirm=true`, write actions return `confirmation_required` with a preview.

## Tests (the proof)

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

What the suite proves:
1. All **87 skills** load from the catalog with valid MCP tool schemas.
2. `github.search_repositories` performs a **live** `api.github.com` call.
3. Missing credentials → structured `credentials_missing` (honest, never fake).
4. Write without `confirm=true` → `confirmation_required` (isolation enforced).
5. Full MCP server boots over **stdio**, serves 87 tools, executes a live call.

## Adding a driver

1. Copy `skillhub/skills/github.py` as your template.
2. Set `SKILL`, `REQUIRED_ENV`, `SETUP_HELP`, and `ACTIONS`.
3. If the skill name contains a hyphen, add it to `MODULE_OVERRIDES` in `registry.py`.
4. Add tests in `tests/test_runtime.py` and run the suite.

## Design notes

- `skillhub/errors.py` — every failure is a machine-readable dict.
- `skillhub/http.py` — shared async HTTP with upstream-error mapping and
  explicit proxy handling (works around an httpx IPv6 `no_proxy` parsing bug).
- `skillhub/registry.py` — discovers skills from `../skills/*/SKILL.md`
  frontmatter, so the tool surface always matches the catalog.
- `skillhub/server.py` — MCP server over stdio (works with Claude Desktop
  and any MCP client).

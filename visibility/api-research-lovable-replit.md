# API Research: Lovable & Replit — 2026-10-02

Re-verification (from scratch) of whether Lovable and Replit expose a public,
programmatic API usable by an AI-agent driver. Same treatment as the Granola
discovery in v1.5.0: previously "no public API" claims re-checked against
current official documentation.

**Bottom line: both are now BUILDABLE.** Neither remains impossible.

---

## 1. Lovable (lovable.dev) — VERDICT: BUILDABLE

### Official docs (verified 2026-10-02)
- REST API overview: https://docs.lovable.dev/integrations/lovable-api
- API basics (base URL, headers, auth, rate limits, pagination, errors): https://docs.lovable.dev/api-reference/introduction
- Official MCP server: https://docs.lovable.dev/integrations/lovable-mcp-server
- Postman collection: Lovable API collection on the Postman API Network (linked from the API docs page)

### Auth
- Workspace-scoped API keys, sent in the `Lovable-API-Key` request header. Keys start with `lov_`.
- Keys are created in **Workspace settings → Access tokens**.
- Requirements: **Business or Enterprise plan** + workspace **owner or admin** role + verified account email.
- Optional `Lovable-Version` header pins the API version as `YYYY-MM-DD` (current default stable: `2026-09-11`).
- Error model: standard envelope with stable `type` token (`unauthorized`, `insufficient_scope`, `payment_required`, `rate_limited`, …); `402 payment_required` when the workspace plan lacks the feature.

### Core endpoints (REST, base `https://api.lovable.dev`, versioned `/v1`)
Official resource areas per the docs; paths below are community-verified against
production (lovagentic docs, 2026; independent live-research notes, 2026-07):

| Method & path | Purpose |
|---|---|
| `GET /v1/me` | Authenticated user profile + workspaces |
| `GET /v1/workspaces` | List workspaces (id, name, plan, credit limits) |
| `GET /v1/workspaces/{wsId}/projects` | List/search projects in a workspace |
| `GET /v1/projects/{pid}` | Project details (status, publish state, preview/screenshot URLs) |
| `POST /v1/projects/{pid}/deployments` | Publish project → `202 { deployment_id, status: "pending", url }` |
| `PATCH /v1/projects/{project_id}` | Update project (e.g. `{"visibility": "workspace_view"}`) — official docs example |
| `POST /v1/projects/{pid}/messages` | Send a chat/build message to the project agent |

### Rate limits & pagination
- Sliding-window rate limits; responses carry `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; `429` with `Retry-After` when exceeded. Each API key has its own bucket.
- Cursor pagination on list endpoints: `limit` 1–100 (default 50), `pagination.next_cursor` / `has_more`.
- Some reads are eventually consistent (project/member lists).

### Gotchas
- **Plan gate:** REST API keys require Business/Enterprise. Free/Pro users cannot mint keys.
- **Scope of the REST API:** "The public API manages and deploys existing projects… AI project creation and editing are available through the Lovable MCP server." Deployment builds do **not** consume AI build credits; per-key monthly credit caps are configurable.
- **Enterprise-only endpoints:** reading a project's PII labels and the per-project security inventory.
- Alternative programmatic path with **no plan gate**: the official MCP server at `https://mcp.lovable.dev` (OAuth, all plans) exposing `list_projects`, `create_project`, `send_message`, `get_diff`, `deploy_project`, etc. Lovable publishes a matching skill file at `mcp.lovable.dev/skill.md`.
- Security history note: Lovable had public BOLA/API incidents in early 2026 (The Register, 2026-04-21); private-by-default since Dec 2025. Drivers should treat project visibility conservatively.

### Driver sketch
`lovable` driver: credential manager holds `lov_` key → `Lovable-API-Key` header (+ pinned `Lovable-Version`). Actions: `list_projects`, `get_project`, `publish_project` (202 → poll deploy status), `update_project`, `get_workspaces`. Plan-gate failures surface as `402` with a clear "requires Business/Enterprise" message.

---

## 2. Replit (replit.com) — VERDICT: BUILDABLE (Enterprise-gated)

### Official docs (verified 2026-10-02)
- Admin API: https://docs.replit.com/teams/admin-api
- Endpoint reference / developer documentation: `api.replit.com` (linked from the Admin API page; OpenAPI served at `https://api.replit.com/openapi.json` without credentials)
- Replit MCP Server: https://docs.replit.com/platforms/mcp-server (announced 2026-09-11)

### Auth (Admin API)
- Scoped API keys created by **account admins on Enterprise accounts** only. Workspace admins and regular members cannot create keys or access the API.
- Scopes include `read:*`, `write:budgets`, `write:deployments`, `write:members`, `compliance:messages:read`, `audit-logs:read`.
- Unauthenticated requests return `{"error":{"code":"unauthenticated","message":"No API key provided."}}`.

### Core endpoints (Admin API, base `https://api.replit.com`)
Paths per the publicly served OpenAPI document and matching community skill mirrors:

| Method & path | Scope | Purpose |
|---|---|---|
| `GET /workspaces` | `read:*` | Account workspace directory (`search` filter) |
| `GET /projects` | `read:*` | Projects across Team Workspaces (`workspaceId`, `search`, `hasDeployment` filters) |
| `GET /deployments` | `read:*` | Deployments in a workspace (`projectId`, `status` filters) |
| `GET /deployments/{deploymentId}` | `read:*` | Single deployment status |
| `GET /usage` | `read:*` | Cost/usage grouped by member/project/workspace/timeseries |
| `POST /budgets` | `write:budgets` | Set/replace/clear budgets (idempotent desired-state) |

### Rate limits & pagination
- Responses include rate-limit headers and `X-Request-Id`. Cursor pagination: `limit` default 50, max 100 (`pagination.cursor` / `hasMore`).

### Gotchas
- **Enterprise-only.** No public REST API exists for regular (Core/free) Replit users — the old "no API" claim is still effectively true for non-Enterprise accounts.
- **Read/admin-oriented:** the Admin API covers reporting, governance, budgets, deployments, and compliance — it does **not** offer arbitrary project code execution or workspace shell access.
- **No deployment-log API:** community operators note Replit exposes no API/CLI/SSH/log-drain for deployment logs (7-day retention, browser only); programmatic log access requires app-level log forwarding.
- Alternative programmatic path with **no Enterprise gate**: the official Replit MCP Server at `https://mcp.replit.com/server/mcp` (Streamable HTTP, OAuth via protected-resource discovery) — "create, find, inspect, update, and publish Replit Apps" from ChatGPT, Claude, Slack, Codex, Claude Code, or any compatible MCP client.

### Driver sketch
`replit` driver: credential manager holds Enterprise Admin API key → scoped Bearer auth against `https://api.replit.com`. Actions: `list_workspaces`, `list_projects`, `list_deployments`, `get_deployment`, `get_usage`, `set_budget` (write-gated). Non-Enterprise users get a clear "requires Enterprise account admin" error with the MCP-server alternative documented. A second, OAuth-based path via the Replit MCP server covers app create/publish for regular users.

---

## Evidence log (2026-10-02)
- `https://docs.lovable.dev/integrations/lovable-api` — "The Lovable API is a REST API that lets you deploy Lovable projects, manage your workspace, monitor security, and embed projects…" (fetched)
- `https://docs.lovable.dev/api-reference/introduction` — base URL `https://api.lovable.dev`, `Lovable-API-Key` header, key creation requirements, sliding-window rate limits, cursor pagination, `2026-09-11` default version (fetched)
- `https://docs.lovable.dev/integrations/lovable-mcp-server` — MCP server at `https://mcp.lovable.dev`, OAuth, all plans, full tool table (fetched)
- `https://docs.replit.com/teams/admin-api` — "available only to account admins on Enterprise accounts… scope-based, programmatic access" (fetched)
- `https://docs.replit.com/updates/2026/09/11/changelog` — Replit MCP Server launch, Sept 2026 (search snippet)
- `https://docs.replit.com/platforms/mcp-server` — `https://mcp.replit.com/server/mcp`, Streamable HTTP, OAuth (search snippet)
- Community mirrors of `https://api.replit.com/openapi.json` endpoint surface (GitHub skill docs, 2026) — paths cross-checked across two independent mirrors.
- Community-verified Lovable endpoint paths (GitHub: lovagentic docs; independent live-research notes, 2026-07-08).

## Recommendation for the skill hub
1. Upgrade both `lovable` and `replit` from honest-stub to real drivers in the next minor version (new branch + certification pass; v2.2.1 stays frozen).
2. `lovable`: REST driver behind plan-gate detection (`402` → clear message); document the all-plans MCP-server alternative in SKILL.md.
3. `replit`: Admin-API driver behind Enterprise-gate detection (`unauthenticated`/403 → clear message); document the MCP-server alternative for regular users.
4. `muse-early-access` remains the only truly impossible stub (Meta-internal).

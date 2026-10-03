---
name: "replit"
title: "Replit"
description: "Replit cloud IDE. Executable driver for the official Replit Admin API (api.replit.com): workspaces, projects, deployments, usage, budgets. Requires an Enterprise account admin API key."
version: "1.2.0"
license: "AGPL-3.0-only"
compatibility: "Any LLM with tool/function calling"
---

# Replit

Replit cloud IDE. This skill has an **executable driver** for the official Replit
Admin API (`https://api.replit.com`, docs: https://docs.replit.com/teams/admin-api,
OpenAPI: https://api.replit.com/openapi.json).

## Setup

1. An **account admin on a Replit Enterprise account** creates a scoped Admin API key.
2. Set the `REPLIT_API_KEY` environment variable (or store it in the runtime's
   credential manager).

Regular (non-Enterprise) users cannot create API keys — the driver says so
plainly on auth failure. The no-Enterprise-gate alternative is the official
Replit MCP server at `https://mcp.replit.com/server/mcp` (Streamable HTTP, OAuth),
which covers create/find/inspect/update/publish of Replit Apps.

Scope note: the Admin API covers reporting, governance, budgets, deployments and
compliance. It does NOT offer arbitrary code execution or shell access, and there
is no deployment-log API (logs are browser-only, 7-day retention).

## Fallback: Push to GitHub

Every Repl can push to GitHub (Repl → Version control → Connect to GitHub).
Once pushed, code-level work can go through the `github` skill instead. This is
a fallback, not the primary path.

## Actions (executable driver)

| Action | Type | Description |
|---|---|---|
| `list_workspaces` | read | List account workspaces (`search`, pagination). |
| `list_projects` | read | List projects across Team Workspaces (`workspace_id`, `search`, `has_deployment`). |
| `list_deployments` | read | List deployments in a workspace (`project_id`, `status`). |
| `get_deployment` | read | Get one deployment's status. |
| `get_usage` | read | Cost/usage grouped by member, project, workspace or timeseries. |
| `set_budget` | write | Set, replace or clear a budget (idempotent desired-state; needs `write:budgets` scope). |

Write actions require explicit approval per the runtime's permission model.

## When to Use This Skill

Activate this skill when the user's request matches:
- Read, create, update, and publish apps through Replit's official MCP server.

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Relevant API access or tool integration for the target service
- Ability to make HTTP requests and parse JSON responses

## Capabilities Required

- [ ] Function/tool calling (to invoke APIs)
- [ ] HTTP requests (to call external services)
- [ ] JSON parsing (to handle API responses)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

When the user requests something matching this skill, follow these steps:

### Step 1: Understand the Request
- Parse what the user wants. Identify key entities (names, dates, IDs, queries).
- If critical information is missing, ask for it. Do not guess IDs, dates, or credentials.

### Step 2: Verify Access
- Check if you have the necessary credentials/integration configured.
- If not connected, explain what the user needs to do (e.g., "Connect your account in settings").
- Never claim you can access something you cannot verify.

### Step 3: Plan the Action
- Break the request into steps: what to read first, what to change (if any).
- For read operations: proceed directly.
- For write operations (create, update, delete, send, post, book): 
  - Summarize what you are about to do
  - Ask for explicit confirmation before executing
  - Never perform destructive actions without confirmation

### Step 4: Execute
- Make the necessary API calls or tool invocations.
- Handle errors gracefully: if something fails, report what failed and why.
- Respect rate limits: do not spam APIs.

### Step 5: Report
- Summarize what was done in the user's language.
- Include key details (IDs, URLs, timestamps) the user may need.
- If something is still pending or needs follow-up, say so clearly.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "replit"
parameters:
  # Add specific parameters based on the user's request
  # Example: query, user_id, date_range, etc.
  query: "user's request in structured form"
```

## Output Pattern

```yaml
# What to return to the user
success: true/false
result: "human-readable summary"
details:
  # Include verifiable details: IDs, URLs, timestamps
  source: "where the data came from"
  checked_at: "ISO-8601 timestamp"
```

## Safety Rules

1. **Never invent data**: If an API returns no results, say so. Do not fabricate.
2. **Separate read from write**: Reads are safe. Writes (create/update/delete/send) ALWAYS need user confirmation.
3. **Protect credentials**: Never log, display, or share API keys, tokens, or passwords.
4. **Respect privacy**: Only access data the user has authorized. Do not access other users' data.
5. **Handle errors honestly**: Report failures with the actual error, not a generic message.

## Example

**User**: "Help me with replit"

**LLM**: 
1. Checks if the required integration is available
2. If yes: "I can help with that. What specifically do you need?"
3. If no: "To help with replit, I need [X] connected. Here's how to set it up..."

---

*This is a universal, LLM-agnostic skill definition. Adapt the API calls to your host environment's available tools.*

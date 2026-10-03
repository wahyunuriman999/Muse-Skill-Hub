---
name: "lovable"
title: "Lovable"
description: Lovable AI app builder. Executable driver for the official Lovable REST API (api.lovable.dev/v1): list workspaces/projects, publish, update, and message projects. Requires a Business/Enterprise plan API key.
version: "1.2.0"
license: "AGPL-3.0-only"
compatibility: "Any LLM with tool/function calling"
---

# Lovable

Lovable AI app builder. This skill has an **executable driver** for the official
Lovable REST API (`https://api.lovable.dev/v1`, docs:
https://docs.lovable.dev/integrations/lovable-api).

## Setup

1. In Lovable, open **Workspace settings → Access tokens** and create an API key
   (format `lov_...`). This requires a **Business or Enterprise** plan and a
   workspace owner/admin role.
2. Set the `LOVABLE_API_KEY` environment variable (or store it in the runtime's
   credential manager).

If the workspace is on a Free/Pro plan, the API returns `402 payment_required`
and the driver tells you so plainly. The plan-free alternative is the official
Lovable MCP server at `https://mcp.lovable.dev` (OAuth, all plans), which covers
project creation/editing — the REST API manages and deploys *existing* projects.

## Fallback: GitHub Sync

Lovable projects can also sync to GitHub (Project settings → GitHub → Connect).
Once synced, code-level work can go through the `github` skill instead. This is
a fallback, not the primary path — the driver above is the primary path.

## Actions (executable driver)

| Action | Type | Description |
|---|---|---|
| `list_workspaces` | read | List workspaces visible to the API key (id, name, plan). |
| `list_projects` | read | List/search projects in a workspace (`workspace_id`, pagination). |
| `get_project` | read | Get one project (status, publish state, preview/screenshot URLs). |
| `publish_project` | write | Publish (deploy) a project. Returns the accepted deployment; poll `get_project` for publish state (the API exposes no deployment-status endpoint). |
| `update_project` | write | Update a project (`visibility`: private / workspace_view / public; `name`). |
| `send_project_message` | write | Send a chat/build message to the project's AI agent. |

Write actions require explicit approval per the runtime's permission model.

## When to Use This Skill

Activate this skill when the user's request matches:
- Manage Lovable projects: list workspaces/projects, publish (deploy), update visibility/name, send build messages to the project agent.

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
skill: "lovable"
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

**User**: "Help me with lovable"

**LLM**: 
1. Checks if the required integration is available
2. If yes: "I can help with that. What specifically do you need?"
3. If no: "To help with lovable, I need [X] connected. Here's how to set it up..."

---

*This is a universal, LLM-agnostic skill definition. Adapt the API calls to your host environment's available tools.*

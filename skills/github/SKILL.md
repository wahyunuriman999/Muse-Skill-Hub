---
name: "github"
title: "GitHub"
description: "Search and work with the user's GitHub repositories through GitHub's official MCP server."
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# GitHub

Search and work with the user's GitHub repositories through GitHub's official MCP server.

## When to Use This Skill

Activate this skill when the user's request matches:
- Search and work with the user's GitHub repositories through GitHub's official MCP server.

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Ability to make HTTP requests to api.github.com (or use a GitHub SDK)
- Web browsing or search API access

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
skill: "github"
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

**User**: "Help me with github"

**LLM**: 
1. Checks if the required integration is available
2. If yes: "I can help with that. What specifically do you need?"
3. If no: "To help with github, I need [X] connected. Here's how to set it up..."

---

*This is a universal, LLM-agnostic skill definition. Adapt the API calls to your host environment's available tools.*


## Actions

<!-- Auto-generated from the driver's ActionDef contracts
     (v2.1 doc-sync). Kept in sync by `skillhub validate`. -->

- **create_issue** — Create an issue (needs GITHUB_TOKEN + confirm=true).  
  Risk: `write` · parameters: owner, repo, title, body · required: owner, repo, title
- **get_repository** — Get details of a public repository.  
  Risk: `read` · parameters: owner, repo · required: owner, repo
- **list_issues** — List issues of a repository.  
  Risk: `read` · parameters: owner, repo, state, per_page · required: owner, repo
- **search_repositories** — Search public GitHub repositories by keyword.  
  Risk: `read` · parameters: query, sort, per_page · required: query

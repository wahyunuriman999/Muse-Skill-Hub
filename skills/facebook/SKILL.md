---
name: "facebook"
title: "Facebook"
description: "Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public events happening near a place, nearby, or in a local area on a date, or to create, edit, publish, or delete their own Marketplace listings. To find, browse, or buy Marketplace listings, use shopping instead. Use pages commands for managed Facebook Page discovery, insights, native draft editing/deletion, same-draft publication, approved posts and native scheduling."
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Facebook

Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public events happening near a place, nearby, or in a local area on a date, or to create, edit, publish, or delete their own Marketplace listings. To find, browse, or buy Marketplace listings, use shopping instead. Use pages commands for managed Facebook Page discovery, insights, native draft editing/deletion, same-draft publication, approved posts and native scheduling.

## When to Use This Skill

Activate this skill when the user's request matches:
- Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, e

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- API credentials or OAuth for the target platform

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
skill: "facebook"
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

**User**: "Help me with facebook"

**LLM**: 
1. Checks if the required integration is available
2. If yes: "I can help with that. What specifically do you need?"
3. If no: "To help with facebook, I need [X] connected. Here's how to set it up..."

---

*This is a universal, LLM-agnostic skill definition. Adapt the API calls to your host environment's available tools.*


## Actions

<!-- Auto-generated from the driver's ActionDef contracts
     (v2.1 doc-sync). Kept in sync by `skillhub validate`. -->

- **get_posts** — List recent posts from the profile/Page feed.  
  Risk: `read` · parameters: limit · required: none
- **get_profile** — Get the connected Facebook profile.  
  Risk: `read` · parameters: none · required: none
- **post_to_feed** — Publish a post to the feed (needs confirm=true).  
  Risk: `write` · parameters: message · required: message

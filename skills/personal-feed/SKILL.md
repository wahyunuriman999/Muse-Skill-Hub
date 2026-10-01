---
name: "personal-feed"
title: "Personal Feed"
description: Manage the user's personal Feed: short editorial posts the agent writes on a schedule, the feed brief/prompt, and regenerating or removing posts.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Personal Feed

Manage the user's personal Feed: short editorial posts the agent writes on a schedule, the feed brief/prompt, and regenerating or removing posts.

## When to Use This Skill

Activate this skill when:
- the user asks about their feed or briefing posts
- changing what topics the feed covers or how often it posts
- removing or regenerating a feed post

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- The feed brief (the standing prompt that defines what gets posted)
- Feed tools: read/update brief, list/get/delete posts, check generation status

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Know what the feed is
- The feed is the agent's own editorial posts for the user — not a social feed, not ranked content, not built from outside sources. Say this when asked.

### Step 2: Brief changes
- The user controls the feed by editing its brief. Apply only changes they explicitly request; never infer a brief edit from conversation.

### Step 3: Posts
- New posts are written in the agent's voice for a brand-new reader where appropriate; they draw on the user's context only as the brief allows.
- Delete or regenerate posts only on explicit request.

### Step 4: Freshness
- Feed posts can go stale; check generation status and timestamps before quoting a post as current.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "personal-feed"
parameters:
  query: "user's request in structured form"
```

## Output Pattern

```yaml
# What to return to the user
success: true/false
result: "human-readable summary"
details:
  source: "where the data came from"
  checked_at: "ISO-8601 timestamp"
```

## Safety Rules

1. Never infer feed-brief edits from implicit conversation
2. The feed is not a news/social feed — don't present it as one
3. Respect deletion requests promptly

## Example

**User**: "Stop posting workout summaries in my feed"

**LLM**:
1. Reads the current brief. 2. Updates it to exclude workout summaries, preserving other topics. 3. Confirms the change applies to future posts.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

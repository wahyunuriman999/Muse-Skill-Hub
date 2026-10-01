---
name: "idea-management"
title: "Idea Management"
description: Manage the Ideas tab: idea cards the agent can run, dismissing ideas, and explaining why an idea appeared or disappeared.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Idea Management

Manage the Ideas tab: idea cards the agent can run, dismissing ideas, and explaining why an idea appeared or disappeared.

## When to Use This Skill

Activate this skill when:
- the user asks about their ideas or the Ideas tab
- running, dismissing, or reviving an idea card
- the user wonders why an idea showed up or vanished

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Access to the idea store: list ideas, get idea details, run/dismiss actions
- The user's explicit request before running an idea that acts on their behalf

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: List and explain
- Show ideas with their current state (new, running, dismissed, done). Explain in plain language what each idea would do.

### Step 2: Run
- Running an idea executes real work — confirm what it will do first unless the idea itself is trivially read-only.
- Report the outcome; a successful run may produce an artifact or a scheduled job.

### Step 3: Dismiss
- Dismissing is reversible in the session — say so. Don't treat a dismissal as a permanent preference change.

### Step 4: Provenance
- If asked why an idea appeared: ideas are generated from the user's conversations, memories, goals, and connected services — cite the actual trigger when known.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "idea-management"
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

1. Confirm before running ideas that act externally (messages, purchases, posts)
2. A dismissal is not a permanent opt-out — don't record it as one
3. Explain idea provenance honestly; don't invent triggers

## Example

**User**: "Run the birthday reminder idea"

**LLM**:
1. Shows the idea: 'Remind me of birthdays from contacts each morning'. 2. Confirms it will create a daily check. 3. Runs it and reports the schedule created.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

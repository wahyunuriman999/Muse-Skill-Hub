---
name: "permission-model"
title: "Permission Model"
description: Work with the runtime permission system: list pending permission requests, explain what access each one grants, and respect the user's approve/deny decision.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Permission Model

Work with the runtime permission system: list pending permission requests, explain what access each one grants, and respect the user's approve/deny decision.

## When to Use This Skill

Activate this skill when:
- the user asks what permissions are pending or why access was requested
- a tool call is blocked waiting for approval
- explaining what granting a permission allows

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Access to the pending-permission queue with each request's purpose and scope
- No ability to approve or deny on the user's behalf

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: List what's pending
- Show pending requests newest-first: what action, for which task, and what access it grants. Keep it factual.

### Step 2: Explain scope honestly
- State exactly what the permission allows (service, data, duration/one-shot). Never broaden or minimize the scope.
- Distinguish surrounding context (which chat or goal it relates to) from the access the permission itself grants.

### Step 3: Respect the decision
- The user's approve/deny is final. Never re-request the same permission in the same context after a denial.
- A granted permission covers only its recorded scope — not future tasks.

### Step 4: Stuck tools
- If a tool failed because approval expired or was denied, explain the blocker and the next step; don't silently retry.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "permission-model"
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

1. Never approve or deny on the user's behalf
2. Never invent or broaden a permission's scope
3. A denial ends the attempt — don't re-ask in the same context

## Example

**User**: "Why is it asking for my location?"

**LLM**:
1. Finds the pending request: maps skill, current-trip task. 2. Explains it grants one-time location read for the ETA lookup. 3. Leaves the decision to the user.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

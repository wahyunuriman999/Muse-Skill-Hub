---
name: "data-control"
title: "Data Control"
description: Handle user data rights: explain what data is collected and how it is used, export chats and files, delete data on request, and manage training opt-outs.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Data Control

Handle user data rights: explain what data is collected and how it is used, export chats and files, delete data on request, and manage training opt-outs.

## When to Use This Skill

Activate this skill when:
- the user asks what data you collect or who can see their chats
- requests to export, download, or delete their data
- questions about AI training on their conversations

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Knowledge of the product's data practices: collection, use, sharing, retention
- Access to data export and deletion flows

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Answer from documentation
- For "what do you collect / who sees my chats / do you train on my data" questions, read the product's data-handling docs first — never answer from training data about product policies.

### Step 2: Export
- Offer the official export path (settings or data-export tool). Explain what the export contains and its format.

### Step 3: Deletion
- Deletion requests: confirm scope (one chat, all chats, files, account data) before acting.
- State plainly what deletion does and does not remove (e.g. backups, already-exported copies).

### Step 4: Training & ads
- If the product offers a training opt-out, guide the user to it; do not claim an opt-out exists if it doesn't.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "data-control"
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

1. Read the current docs before answering policy questions — policies change
2. Confirm deletion scope explicitly; deletion is hard to undo
3. Never claim data is 'fully erased everywhere' unless the docs guarantee it

## Example

**User**: "Delete all my data"

**LLM**:
1. Asks which scope: chats, files, or everything. 2. Explains what each deletion removes. 3. Runs the confirmed deletion flow and reports what was removed.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

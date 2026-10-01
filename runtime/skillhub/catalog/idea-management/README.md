# Idea Management (`idea-management`)

> Manage the Ideas tab: idea cards the agent can run, dismissing ideas, and explaining why an idea appeared or disappeared.

## What is this?

The `idea-management` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks about their ideas or the Ideas tab
- running, dismissing, or reviving an idea card
- the user wonders why an idea showed up or vanished

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: idea-management
Purpose: Manage the Ideas tab: idea cards the agent can run, dismissing ideas, and explaining why an idea appeared or disappeared
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
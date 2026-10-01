# Permission Model (`permission-model`)

> Work with the runtime permission system: list pending permission requests, explain what access each one grants, and respect the user's approve/deny decision.

## What is this?

The `permission-model` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks what permissions are pending or why access was requested
- a tool call is blocked waiting for approval
- explaining what granting a permission allows

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: permission-model
Purpose: Work with the runtime permission system: list pending permission requests, explain what access each one grants, and resp
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
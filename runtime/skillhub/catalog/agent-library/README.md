# Agent Library (`agent-library`)

> Manage the user's file library: uploads, generated artifacts, expiring public share links, and the media collection. Know where files live and how the user gets them back.

## What is this?

The `agent-library` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks about their files, library, uploads, or downloads
- sharing a file publicly or generating a download link
- the user can't find a file the agent created

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: agent-library
Purpose: Manage the user's file library: uploads, generated artifacts, expiring public share links, and the media collection. Kno
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
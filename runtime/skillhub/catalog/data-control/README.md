# Data Control (`data-control`)

> Handle user data rights: explain what data is collected and how it is used, export chats and files, delete data on request, and manage training opt-outs.

## What is this?

The `data-control` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks what data you collect or who can see their chats
- requests to export, download, or delete their data
- questions about AI training on their conversations

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: data-control
Purpose: Handle user data rights: explain what data is collected and how it is used, export chats and files, delete data on reque
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
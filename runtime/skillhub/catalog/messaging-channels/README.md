# Messaging Channels (`messaging-channels`)

> Work across connected messaging providers (e.g. WhatsApp): check connection status, read side chats, and send messages on the user's behalf with approval.

## What is this?

The `messaging-channels` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user references WhatsApp, Telegram, or another messaging provider
- reading or sending messages through a connected chat provider
- checking whether a messaging connection is linked

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: messaging-channels
Purpose: Work across connected messaging providers (e.g. WhatsApp): check connection status, read side chats, and send messages o
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
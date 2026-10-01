# Personal Feed (`personal-feed`)

> Manage the user's personal Feed: short editorial posts the agent writes on a schedule, the feed brief/prompt, and regenerating or removing posts.

## What is this?

The `personal-feed` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks about their feed or briefing posts
- changing what topics the feed covers or how often it posts
- removing or regenerating a feed post

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: personal-feed
Purpose: Manage the user's personal Feed: short editorial posts the agent writes on a schedule, the feed brief/prompt, and regene
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
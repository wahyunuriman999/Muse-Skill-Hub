# Messenger (`messenger`)

> Work with the user's Messenger account: read call history; read and search contacts; read, search, and summarize conversations; send, react to, unsend, or edit messages; and message Marketplace listing threads.

## What is this?

The `messenger` skill is one of Muse's capabilities.

Official description: Work with the user's Messenger account: read call history; read and search contacts; read, search, and summarize conversations; send, react to, unsend, or edit messages; and message Marketplace listing threads.

## When to use?

When the user asks about social media content or posting.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: messenger
Purpose: Work with the user's Messenger account: read call history; read and search contacts; read, search, and summarize convers
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
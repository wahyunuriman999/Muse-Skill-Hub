# Ghl (`ghl`)

> Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog.

## What is this?

The `ghl` skill is one of Muse's capabilities.

Official description: Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog.

## When to use?

When the user's request matches: Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: ghl
Purpose: Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
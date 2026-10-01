# Asana (`asana`)

> Capability for asana

## What is this?

The `asana` skill is one of Muse's capabilities.

Official description: Capability for asana

## When to use?

When the user's request matches: Capability for asana

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: asana
Purpose: Capability for asana
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
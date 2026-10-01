# Lovable (`lovable`)

> Capability for lovable

## What is this?

The `lovable` skill is one of Muse's capabilities.

Official description: Capability for lovable

## When to use?

When the user's request matches: Capability for lovable

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: lovable
Purpose: Capability for lovable
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Canva (`canva`)

> Capability for canva

## What is this?

The `canva` skill is one of Muse's capabilities.

Official description: Capability for canva

## When to use?

When the user's request matches: Capability for canva

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: canva
Purpose: Capability for canva
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
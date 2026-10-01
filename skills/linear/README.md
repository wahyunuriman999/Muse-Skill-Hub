# Linear (`linear`)

> Track engineering work in Linear: create and list issues, set priorities, manage cycles, and follow project status.

## What is this?

The `linear` skill is one of Muse's capabilities.

Official description: Capability for linear

## When to use?

When the user's request matches: Capability for linear

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: linear
Purpose: Capability for linear
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
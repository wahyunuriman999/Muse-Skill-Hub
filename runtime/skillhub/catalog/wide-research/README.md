# Wide Research (`wide-research`)

> Use when the user needs broad parallel research across many independent inputs with a shared output schema.

## What is this?

The `wide-research` skill is one of Muse's capabilities.

Official description: Use when the user needs broad parallel research across many independent inputs with a shared output schema.

## When to use?

When the user's request matches: Use when the user needs broad parallel research across many independent inputs with a shared output 

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: wide-research
Purpose: Use when the user needs broad parallel research across many independent inputs with a shared output schema.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Muse_Db (`muse_db`)

> Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built product tools do not expose the needed state.

## What is this?

The `muse_db` skill is one of Muse's capabilities.

Official description: Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built product tools do not expose the needed state.

## When to use?

When the user's request matches: Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built produc

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: muse_db
Purpose: Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built product tools do not expos
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
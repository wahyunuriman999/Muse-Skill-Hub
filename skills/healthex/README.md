# HealthEx (`healthex`)

> Use to connect HealthEx and ask questions about your medications, lab results, and other health records.

## What is this?

The `healthex` skill is one of Muse's capabilities.

Official description: Use to connect HealthEx and ask questions about your medications, lab results, and other health records.

## When to use?

When the user's request matches: Use to connect HealthEx and ask questions about your medications, lab results, and other health reco

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: healthex
Purpose: Use to connect HealthEx and ask questions about your medications, lab results, and other health records.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
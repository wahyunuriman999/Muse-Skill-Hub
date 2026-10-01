# Tessie (`tessie`)

> Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints.

## What is this?

The `tessie` skill is one of Muse's capabilities.

Official description: Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints.

## When to use?

When the user's request matches: Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: tessie
Purpose: Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
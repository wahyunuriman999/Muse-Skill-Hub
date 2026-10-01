# OpenTable (`opentable`)

> Find restaurants on OpenTable, check availability, and make, change, or cancel reservations. Use for restaurant booking and live reservation data.

## What is this?

The `opentable` skill is one of Muse's capabilities.

Official description: Find restaurants on OpenTable, check availability, and make, change, or cancel reservations. Use for restaurant booking and live reservation data.

## When to use?

When the user asks to search, book, or manage travel/dining.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: opentable
Purpose: Find restaurants on OpenTable, check availability, and make, change, or cancel reservations. Use for restaurant booking 
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
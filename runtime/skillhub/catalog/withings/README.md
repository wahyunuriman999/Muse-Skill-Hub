# Withings (`withings`)

> Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, and intraday data.

## What is this?

The `withings` skill is one of Muse's capabilities.

Official description: Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, and intraday data.

## When to use?

When the user's request matches: Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, an

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: withings
Purpose: Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, and intraday data.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
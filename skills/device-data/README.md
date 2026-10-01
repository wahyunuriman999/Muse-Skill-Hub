# Device Data (`device-data`)

> Read cached contacts and calendar events from Muse storage. Delete Muse's local copy of either source without modifying paired devices.

## What is this?

The `device-data` skill is one of Muse's capabilities.

Official description: Read cached contacts and calendar events from Muse storage. Delete Muse's local copy of either source without modifying paired devices.

## When to use?

When the user asks about schedules, events, or time management.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: device-data
Purpose: Read cached contacts and calendar events from Muse storage. Delete Muse's local copy of either source without modifying 
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
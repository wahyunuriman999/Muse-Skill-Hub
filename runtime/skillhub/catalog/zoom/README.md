# Zoom (`zoom`)

> Manage Zoom: schedule and list meetings, fetch recordings, and manage meeting settings.

## What is this?

The `zoom` skill is one of Muse's capabilities.

Official description: Capability for zoom

## When to use?

When the user's request matches: Capability for zoom

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: zoom
Purpose: Capability for zoom
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
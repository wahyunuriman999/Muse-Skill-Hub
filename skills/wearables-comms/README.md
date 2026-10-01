# Wearables Calls and Messages (`wearables-comms`)

> Capability for wearables-comms

## What is this?

The `wearables-comms` skill is one of Muse's capabilities.

Official description: Capability for wearables-comms

## When to use?

When the user's request matches: Capability for wearables-comms

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: wearables-comms
Purpose: Capability for wearables-comms
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
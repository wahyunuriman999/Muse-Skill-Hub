# Wearables Calls and Messages (`wearables-comms`)

> Handle calls and messages through connected wearables: read notifications, place and answer calls, and send quick replies.

## What is this?

The `wearables-comms` skill is one of Muse's capabilities.

Official description: Handle calls and messages through connected wearables: read notifications, place and answer calls, and send quick replies.

## When to use?

When the user wants to handle calls/messages via a connected wearable

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
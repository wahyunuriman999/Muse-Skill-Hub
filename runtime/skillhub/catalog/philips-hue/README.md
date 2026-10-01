# Philips Hue (`philips-hue`)

> Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2.

## What is this?

The `philips-hue` skill is one of Muse's capabilities.

Official description: Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2.

## When to use?

When the user's request matches: Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: philips-hue
Purpose: Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
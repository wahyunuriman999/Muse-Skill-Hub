# Wearable Device Skills (`wearable-device-skills`)

> Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published by a paired phone or wearable, including device controls, app actions, camera or media actions, and smart-home actions.

## What is this?

The `wearable-device-skills` skill is one of Muse's capabilities.

Official description: Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published by a paired phone or wearable, including device controls, app actions, camera or media actions, and smart-home actions.

## When to use?

When the user's request matches: Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published b

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: wearable-device-skills
Purpose: Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published by a paired phone or 
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
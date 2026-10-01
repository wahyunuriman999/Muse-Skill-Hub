# Voice Design (`voice-design`)

> Choose or design a speaking voice when the user asks for a new, different, custom, invented, or generated voice, or restore the voice used immediately before the current one.

## What is this?

The `voice-design` skill is one of Muse's capabilities.

Official description: Choose or design a speaking voice when the user asks for a new, different, custom, invented, or generated voice, or restore the voice used immediately before the current one.

## When to use?

When the user's request matches: Choose or design a speaking voice when the user asks for a new, different, custom, invented, or gene

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: voice-design
Purpose: Choose or design a speaking voice when the user asks for a new, different, custom, invented, or generated voice, or rest
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
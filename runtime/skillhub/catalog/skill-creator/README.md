# skill-creator (`skill-creator`)

> Create or update a workspace skill: its description, structure, instructions, and supporting files.

## What is this?

The `skill-creator` skill is one of Muse's capabilities. Official description: Create or update a workspace skill: its description, structure, instructions, and supporting files.

## When to use?

When you want to create a new reusable skill from a successful workflow.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: skill-creator
Purpose: Create or update a workspace skill: its description, structure, instructions, and supporting files.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
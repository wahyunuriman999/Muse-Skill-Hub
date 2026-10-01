# Share ideas (`share-ideas`)

> Publish a portable Idea card from the Ideas tab — only after the user explicitly asks to publish it.

## What is this?

The `share-ideas` skill is one of Muse's capabilities.

Official description: Capability for share-ideas

## When to use?

When the user's request matches: Capability for share-ideas

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: share-ideas
Purpose: Capability for share-ideas
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Google Slides (`google-slides`)

> Read, create, and edit the user's Google Slides presentations.

## What is this?

The `google-slides` skill is one of Muse's capabilities.

Official description: Read, create, and edit the user's Google Slides presentations.

## When to use?

When the user's request matches: Read, create, and edit the user's Google Slides presentations.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-slides
Purpose: Read, create, and edit the user's Google Slides presentations.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
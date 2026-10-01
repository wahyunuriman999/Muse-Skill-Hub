# Social Content Performance (`social-content-performance`)

> Analyze the user's own Instagram account and post performance using linked-account analytics.

## What is this?

The `social-content-performance` skill is one of Muse's capabilities.

Official description: Analyze the user's own Instagram account and post performance using linked-account analytics.

## When to use?

When the user asks about social media content or posting.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: social-content-performance
Purpose: Analyze the user's own Instagram account and post performance using linked-account analytics.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
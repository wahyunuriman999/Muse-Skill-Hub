# Google Tasks (`google-tasks`)

> Manage the user's Google Tasks: lists, task details, creation, updates, and completion.

## What is this?

The `google-tasks` skill is one of Muse's capabilities.

Official description: Manage the user's Google Tasks: lists, task details, creation, updates, and completion.

## When to use?

When the user's request matches: Manage the user's Google Tasks: lists, task details, creation, updates, and completion.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-tasks
Purpose: Manage the user's Google Tasks: lists, task details, creation, updates, and completion.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
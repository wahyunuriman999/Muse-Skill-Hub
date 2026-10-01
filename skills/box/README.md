# Box (`box`)

> Search, read, upload, download, move, rename, delete, restore, and share Box content; manage comments and metadata.

## What is this?

The `box` skill is one of Muse's capabilities.

Official description: Search, read, upload, download, move, rename, delete, restore, and share Box content; manage comments and metadata.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: box
Purpose: Search, read, upload, download, move, rename, delete, restore, and share Box content; manage comments and metadata.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
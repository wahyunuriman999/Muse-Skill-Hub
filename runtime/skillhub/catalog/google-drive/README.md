# google-drive (`google-drive`)

> Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.

## What is this?

The `google-drive` skill is one of Muse's capabilities. Official description: Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.

## When to use?

When the user asks to find, read, or manage files in Google Drive.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-drive
Purpose: Work with the user's Google Drive: files, folders, uploads, downloads, and sharing.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
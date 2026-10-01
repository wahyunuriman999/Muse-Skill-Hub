# google-sheets (`google-sheets`)

> Read, write, and manage the user's Google Sheets.

## What is this?

The `google-sheets` skill is one of Muse's capabilities. Official description: Read, write, and manage the user's Google Sheets.

## When to use?

When the user asks to read/write spreadsheets or process tabular data.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-sheets
Purpose: Read, write, and manage the user's Google Sheets.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
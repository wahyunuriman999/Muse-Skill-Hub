# google-calendar (`google-calendar`)

> Work with the user's Google Calendar: agenda views, event details, and scheduling changes.

## What is this?

The `google-calendar` skill is one of Muse's capabilities. Official description: Work with the user's Google Calendar: agenda views, event details, and scheduling changes.

## When to use?

When the user asks to check schedule, create events, or reschedule calendar items.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-calendar
Purpose: Work with the user's Google Calendar: agenda views, event details, and scheduling changes.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
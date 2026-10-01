# gmail (`gmail`)

> Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments.

## What is this?

The `gmail` skill is one of Muse's capabilities. Official description: Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments.

## When to use?

When the user asks to read, search, reply to, or manage Gmail emails.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: gmail
Purpose: Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage la
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
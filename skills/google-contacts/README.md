# Google Contacts (`google-contacts`)

> Search, view, create, update, and delete the user's Google Contacts.

## What is this?

The `google-contacts` skill is one of Muse's capabilities.

Official description: Search, view, create, update, and delete the user's Google Contacts.

## When to use?

When the user's request matches: Search, view, create, update, and delete the user's Google Contacts.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-contacts
Purpose: Search, view, create, update, and delete the user's Google Contacts.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
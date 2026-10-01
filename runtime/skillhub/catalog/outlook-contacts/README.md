# Outlook Contacts (`outlook-contacts`)

> List, search, create, update, and delete contacts in the user's Outlook account.

## What is this?

The `outlook-contacts` skill is one of Muse's capabilities.

Official description: List, search, create, update, and delete contacts in the user's Outlook account.

## When to use?

When the user asks to manage emails.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: outlook-contacts
Purpose: List, search, create, update, and delete contacts in the user's Outlook account.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Outlook Mail (`outlook-mail`)

> Read, search, send, reply to, and delete messages in the user's Outlook Mail.

## What is this?

The `outlook-mail` skill is one of Muse's capabilities.

Official description: Read, search, send, reply to, and delete messages in the user's Outlook Mail.

## When to use?

When the user asks to manage emails.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: outlook-mail
Purpose: Read, search, send, reply to, and delete messages in the user's Outlook Mail.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
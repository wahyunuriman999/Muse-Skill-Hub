# Instagram Messages (`instagram-messages`)

> Use this to interact with the user's Instagram messages. Read inboxes, threads, top recipients, filtered inbox views, DM search results, and send messages through `instagram-messages-cli`.

## What is this?

The `instagram-messages` skill is one of Muse's capabilities.

Official description: Use this to interact with the user's Instagram messages. Read inboxes, threads, top recipients, filtered inbox views, DM search results, and send messages through `instagram-messages-cli`.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: instagram-messages
Purpose: Use this to interact with the user's Instagram messages. Read inboxes, threads, top recipients, filtered inbox views, DM
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
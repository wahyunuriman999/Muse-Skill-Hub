# Calendly (`calendly`)

> View Calendly events and event types, and manage scheduling data using the Calendly CLI.

## What is this?

The `calendly` skill is one of Muse's capabilities.

Official description: View Calendly events and event types, and manage scheduling data using the Calendly CLI.

## When to use?

When the user's request matches: View Calendly events and event types, and manage scheduling data using the Calendly CLI.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: calendly
Purpose: View Calendly events and event types, and manage scheduling data using the Calendly CLI.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
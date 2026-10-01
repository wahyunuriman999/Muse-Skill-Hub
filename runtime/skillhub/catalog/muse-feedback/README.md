# Muse feedback (`muse-feedback`)

> Use for feedback and feature requests to the Muse team. Whenever your response tells the user you can't do a specific thing they wanted, or accepts them giving up on one, offer once to file feedback in that response. This covers missing integrations you can't do yourself, capabilities you lack, and tasks that keep failing at a specific point. File only on their go-ahead. Also use when asked to send, view, check, or withdraw feedback.

## What is this?

The `muse-feedback` skill is one of Muse's capabilities.

Official description: Use for feedback and feature requests to the Muse team. Whenever your response tells the user you can't do a specific thing they wanted, or accepts them giving up on one, offer once to file feedback in that response. This covers missing integrations you can't do yourself, capabilities you lack, and tasks that keep failing at a specific point. File only on their go-ahead. Also use when asked to send, view, check, or withdraw feedback.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: muse-feedback
Purpose: Use for feedback and feature requests to the Muse team. Whenever your response tells the user you can't do a specific th
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
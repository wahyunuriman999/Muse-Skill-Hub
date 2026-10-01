# Google Forms (`google-forms`)

> Read, create, and update the user's Google Forms, and read responses.

## What is this?

The `google-forms` skill is one of Muse's capabilities.

Official description: Read, create, and update the user's Google Forms, and read responses.

## When to use?

When the user's request matches: Read, create, and update the user's Google Forms, and read responses.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-forms
Purpose: Read, create, and update the user's Google Forms, and read responses.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
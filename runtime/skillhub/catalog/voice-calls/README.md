# Voice Calls (`voice-calls`)

> Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow.

## What is this?

The `voice-calls` skill is one of Muse's capabilities.

Official description: Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow.

## When to use?

When the user's request matches: Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: voice-calls
Purpose: Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
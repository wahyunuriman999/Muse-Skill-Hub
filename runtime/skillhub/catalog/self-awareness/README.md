# Self Awareness (`self-awareness`)

> Ground self-referential answers in the agent's actual filesystem. Use when the user asks who the agent is, what it can do, what it knows, what it remembers, what it has built, what services are connected, or what rules it follows.

## What is this?

The `self-awareness` skill is one of Muse's capabilities.

Official description: Ground self-referential answers in the agent's actual filesystem. Use when the user asks who the agent is, what it can do, what it knows, what it remembers, what it has built, what services are connected, or what rules it follows.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: self-awareness
Purpose: Ground self-referential answers in the agent's actual filesystem. Use when the user asks who the agent is, what it can d
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
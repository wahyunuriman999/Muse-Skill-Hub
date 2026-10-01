# Zapier (`zapier`)

> Connect Muse to actions across apps through Zapier's official MCP server.

## What is this?

The `zapier` skill is one of Muse's capabilities.

Official description: Connect Muse to actions across apps through Zapier's official MCP server.

## When to use?

When the user's request matches: Connect Muse to actions across apps through Zapier's official MCP server.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: zapier
Purpose: Connect Muse to actions across apps through Zapier's official MCP server.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
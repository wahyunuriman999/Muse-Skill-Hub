# Evernote (`evernote`)

> Read and create notes through Evernote's official MCP server.

## What is this?

The `evernote` skill is one of Muse's capabilities.

Official description: Read and create notes through Evernote's official MCP server.

## When to use?

When the user's request matches: Read and create notes through Evernote's official MCP server.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: evernote
Purpose: Read and create notes through Evernote's official MCP server.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
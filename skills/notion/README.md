# Notion (`notion`)

> Search, read, create, and update Notion pages via the Notion MCP.

## What is this?

The `notion` skill is one of Muse's capabilities.

Official description: Search, read, create, and update Notion pages via the Notion MCP.

## When to use?

When the user's request matches: Search, read, create, and update Notion pages via the Notion MCP.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: notion
Purpose: Search, read, create, and update Notion pages via the Notion MCP.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
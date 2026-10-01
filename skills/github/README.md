# GitHub (`github`)

> Search and work with the user's GitHub repositories through GitHub's official MCP server.

## What is this?

The `github` skill is one of Muse's capabilities. Official description: Search and work with the user's GitHub repositories through GitHub's official MCP server.

## When to use?

When the user mentions repos, code, PRs, issues, or asks for help with GitHub.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: github
Purpose: Search and work with the user's GitHub repositories through GitHub's official MCP server.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
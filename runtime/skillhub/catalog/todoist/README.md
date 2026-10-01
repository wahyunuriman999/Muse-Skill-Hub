# Todoist (`todoist`)

> Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's official MCP server.

## What is this?

The `todoist` skill is one of Muse's capabilities.

Official description: Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's official MCP server.

## When to use?

When the user's request matches: Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's 

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: todoist
Purpose: Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's official MCP server.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
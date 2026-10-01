# Quickbooks (`quickbooks`)

> Read and manage the user's QuickBooks business through Intuit's official MCP server, including reports, invoices, customers, products, payment links, sales settings, and industry benchmarks.

## What is this?

The `quickbooks` skill is one of Muse's capabilities.

Official description: Read and manage the user's QuickBooks business through Intuit's official MCP server, including reports, invoices, customers, products, payment links, sales settings, and industry benchmarks.

## When to use?

When the user's request matches: Read and manage the user's QuickBooks business through Intuit's official MCP server, including repor

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: quickbooks
Purpose: Read and manage the user's QuickBooks business through Intuit's official MCP server, including reports, invoices, custom
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
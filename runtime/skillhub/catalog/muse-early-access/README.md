# Muse early access (`muse-early-access`)

> Use for questions about Muse's general early access program, requests to join it, checking or withdrawing a join request, and admission updates.

## What is this?

The `muse-early-access` skill is one of Muse's capabilities.

Official description: Use for questions about Muse's general early access program, requests to join it, checking or withdrawing a join request, and admission updates.

## When to use?

When the user's request matches: Use for questions about Muse's general early access program, requests to join it, checking or withdr

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: muse-early-access
Purpose: Use for questions about Muse's general early access program, requests to join it, checking or withdrawing a join request
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
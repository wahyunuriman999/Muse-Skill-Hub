# Klaviyo (`klaviyo`)

> Run Klaviyo email/SMS marketing: manage lists and segments, build campaigns and flows, and edit templates.

## What is this?

The `klaviyo` skill is one of Muse's capabilities.

Official description: Capability for klaviyo

## When to use?

When the user's request matches: Capability for klaviyo

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: klaviyo
Purpose: Capability for klaviyo
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
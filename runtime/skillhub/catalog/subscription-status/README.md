# Subscription Status (`subscription-status`)

> Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available plans and prices, or verify information that references the Muse subscription.

## What is this?

The `subscription-status` skill is one of Muse's capabilities.

Official description: Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available plans and prices, or verify information that references the Muse subscription.

## When to use?

When the user's request matches: Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: subscription-status
Purpose: Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available plans and prices, o
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Wallet (`wallet`)

> Coordinate payments: check wallet connection state, use saved payment methods and addresses through secure provider pages, and run the required purchase review and approval flow.

## What is this?

The `wallet` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user wants to pay, check out, or buy something
- questions about saved cards, payment methods, or shipping addresses
- setting up or disconnecting a payment provider

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: wallet
Purpose: Coordinate payments: check wallet connection state, use saved payment methods and addresses through secure provider page
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
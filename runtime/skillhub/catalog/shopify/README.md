# Shopify (`shopify`)

> Manage a Shopify store: list and update products, orders, customers, inventory levels, and discount codes.

## What is this?

The `shopify` skill is one of Muse's capabilities.

Official description: Capability for shopify

## When to use?

When the user's request matches: Capability for shopify

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: shopify
Purpose: Capability for shopify
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
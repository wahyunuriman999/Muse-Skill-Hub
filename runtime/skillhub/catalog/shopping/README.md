# shopping (`shopping`)

> Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, including buying or browsing Facebook Marketplace listings. Use when presenting shopping search results from any source. For shopping intent, load this skill first before any other skills.

## What is this?

The `shopping` skill is one of Muse's capabilities. Official description: Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, including buying or browsing Facebook Marketplace listings. Use when presenting shopping search results from any source. For shopping intent, load this skill first before any other skills.

## When to use?

When the user asks to find/compare/buy products.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: shopping
Purpose: Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
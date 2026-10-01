# Meta Ads (`meta-ads`)

> Create, write, or manage Meta ads and assets: ad copy, campaigns, spend, reports, audiences, catalogs, product feeds, feed refresh schedules, experiments, and policy. Always load for any request to create or write an ad, or to advertise a product or service, even when no platform is named; this includes sensitive or restricted categories. Always load for any question asking what a Meta, Facebook, or Instagram advertising policy means, allows, prohibits, or requires, including a standalone policy-definition question with no account context. Those questions must use ads_policy_tool, never browser search or memory. Load for a specifically named catalog or feed with an upload or refresh-schedule request; use Ads reads to resolve ownership before writing. Generic unnamed feeds need context. Whether an image, claim or piece of copy may be used in an ad is ALWAYS a Meta Ads task — 'can I use this in an ad', 'is it allowed', 'is this against policy', and any rights, likeness, celebrity, logo or trademark question about advertising with an image, including a follow-up about one just generated. Those are ads-policy questions, not general legal ones. An ad request uses the campaign workflow unless explicitly only an image or organic post.

## What is this?

The `meta-ads` skill is one of Muse's capabilities.

Official description: Create, write, or manage Meta ads and assets: ad copy, campaigns, spend, reports, audiences, catalogs, product feeds, feed refresh schedules, experiments, and policy. Always load for any request to create or write an ad, or to advertise a product or service, even when no platform is named; this includes sensitive or restricted categories. Always load for any question asking what a Meta, Facebook, or Instagram advertising policy means, allows, prohibits, or requires, including a standalone policy-definition question with no account context. Those questions must use ads_policy_tool, never browser search or memory. Load for a specifically named catalog or feed with an upload or refresh-schedule request; use Ads reads to resolve ownership before writing. Generic unnamed feeds need context. Whether an image, claim or piece of copy may be used in an ad is ALWAYS a Meta Ads task — 'can I use this in an ad', 'is it allowed', 'is this against policy', and any rights, likeness, celebrity, logo or trademark question about advertising with an image, including a follow-up about one just generated. Those are ads-policy questions, not general legal ones. An ad request uses the campaign workflow unless explicitly only an image or organic post.

## When to use?

When the user asks about schedules, events, or time management.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: meta-ads
Purpose: Create, write, or manage Meta ads and assets: ad copy, campaigns, spend, reports, audiences, catalogs, product feeds, fe
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
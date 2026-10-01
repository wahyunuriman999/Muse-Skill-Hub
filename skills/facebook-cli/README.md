# Facebook (`facebook-cli`)

> Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public events happening near a place, nearby, or in a local area on a date, or to create, edit, publish, or delete their own Marketplace listings. To find, browse, or buy Marketplace listings, use shopping instead. Use pages commands for managed Facebook Page discovery, insights, native draft editing/deletion, same-draft publication, approved posts and native scheduling.

## What is this?

The `facebook-cli` skill is one of Muse's capabilities.

Official description: Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public events happening near a place, nearby, or in a local area on a date, or to create, edit, publish, or delete their own Marketplace listings. To find, browse, or buy Marketplace listings, use shopping instead. Use pages commands for managed Facebook Page discovery, insights, native draft editing/deletion, same-draft publication, approved posts and native scheduling.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: facebook-cli
Purpose: Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profi
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
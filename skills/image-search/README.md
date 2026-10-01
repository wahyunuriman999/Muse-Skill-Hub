# image-search (`image-search`)

> Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person.

## What is this?

The `image-search` skill is one of Muse's capabilities. Official description: Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person.

## When to use?

When visual references from the web are needed.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: image-search
Purpose: Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not ident
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Media Library (`media-library`)

> Search and inspect the user's photo library, including connected device galleries. Use for photo requests and whenever a photo could ground or personalize a response; lookups of uploaded photos are cheap, so check opportunistically and move on if nothing fits.

## What is this?

The `media-library` skill is one of Muse's capabilities.

Official description: Search and inspect the user's photo library, including connected device galleries. Use for photo requests and whenever a photo could ground or personalize a response; lookups of uploaded photos are cheap, so check opportunistically and move on if nothing fits.

## When to use?

When visual content or image search is needed.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: media-library
Purpose: Search and inspect the user's photo library, including connected device galleries. Use for photo requests and whenever a
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
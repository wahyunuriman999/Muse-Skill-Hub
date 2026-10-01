# Tts (`tts`)

> Turn supplied text into spoken audio, single or multi-speaker. For composed audio content (a podcast, briefing, or narrated summary), use podcast.

## What is this?

The `tts` skill is one of Muse's capabilities.

Official description: Turn supplied text into spoken audio, single or multi-speaker. For composed audio content (a podcast, briefing, or narrated summary), use podcast.

## When to use?

When the user asks about music, audio, or podcasts.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: tts
Purpose: Turn supplied text into spoken audio, single or multi-speaker. For composed audio content (a podcast, briefing, or narra
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
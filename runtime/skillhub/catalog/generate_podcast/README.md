# Generate_Podcast (`generate_podcast`)

> Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts.

## What is this?

The `generate_podcast` skill is one of Muse's capabilities.

Official description: Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts.

## When to use?

When the user asks about music, audio, or podcasts.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: generate_podcast
Purpose: Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# spotify (`spotify`)

> Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify.

## What is this?

The `spotify` skill is one of Muse's capabilities. Official description: Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify.

## When to use?

When the user asks to search music, create playlists, or manage Spotify.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: spotify
Purpose: Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created wi
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
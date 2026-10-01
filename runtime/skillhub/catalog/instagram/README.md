# instagram (`instagram`)

> Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile details, and publish stories, reels, posts, or carousels on request.

## What is this?

The `instagram` skill is one of Muse's capabilities. Official description: Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile details, and publish stories, reels, posts, or carousels on request.

## When to use?

When the user shares an Instagram link or asks to read/post Instagram content.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed (prices, schedules, availability), check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: instagram
Purpose: Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer q
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
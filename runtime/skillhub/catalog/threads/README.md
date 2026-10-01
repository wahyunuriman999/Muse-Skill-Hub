# Threads (`threads`)

> Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish posts on request.

## What is this?

The `threads` skill is one of Muse's capabilities.

Official description: Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish posts on request.

## When to use?

When the user asks to manage files or cloud storage.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: threads
Purpose: Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search,
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
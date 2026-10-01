# Travel Planning (`travel-planning`)

> Use this skill when an active or proposed trip needs planning, logistics, feasibility, entry or transit checks, itinerary work, or investigation of an airport process, immigration, ground transport, a transfer, or fast-track service, even for a narrow question with no booking intent. Route a bounded flight, hotel, restaurant, event, or other item ready for live availability or booking directly to Booking. Skip this skill for a stable travel fact alone or flight status.

## What is this?

The `travel-planning` skill is one of Muse's capabilities.

Official description: Use this skill when an active or proposed trip needs planning, logistics, feasibility, entry or transit checks, itinerary work, or investigation of an airport process, immigration, ground transport, a transfer, or fast-track service, even for a narrow question with no booking intent. Route a bounded flight, hotel, restaurant, event, or other item ready for live availability or booking directly to Booking. Skip this skill for a stable travel fact alone or flight status.

## When to use?

When the user asks to search, book, or manage travel/dining.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: travel-planning
Purpose: Use this skill when an active or proposed trip needs planning, logistics, feasibility, entry or transit checks, itinerar
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
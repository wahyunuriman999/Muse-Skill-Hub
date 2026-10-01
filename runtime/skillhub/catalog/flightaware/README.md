# FlightAware AeroAPI (`flightaware`)

> Use for questions about a specific flight’s departure or arrival time, including “when’s my flight?” and confirmation of remembered times, plus flight status, delays, and cancellations. Verify the exact dated flight before answering; memory identifies the itinerary but does not verify its current schedule. Use FlightAware to monitor operational changes for an upcoming booked flight when the user directly asks for ongoing monitoring.

## What is this?

The `flightaware` skill is one of Muse's capabilities.

Official description: Use for questions about a specific flight’s departure or arrival time, including “when’s my flight?” and confirmation of remembered times, plus flight status, delays, and cancellations. Verify the exact dated flight before answering; memory identifies the itinerary but does not verify its current schedule. Use FlightAware to monitor operational changes for an upcoming booked flight when the user directly asks for ongoing monitoring.

## When to use?

When the user asks about schedules, events, or time management.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: flightaware
Purpose: Use for questions about a specific flight’s departure or arrival time, including “when’s my flight?” and confirmation of
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Health Connect (`google-health-connect`)

> The user's synced Google Health Connect data from their Android device: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts.

## What is this?

The `google-health-connect` skill is one of Muse's capabilities.

Official description: The user's synced Google Health Connect data from their Android device: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts.

## When to use?

When the user's request matches: The user's synced Google Health Connect data from their Android device: daily metrics (steps, distan

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: google-health-connect
Purpose: The user's synced Google Health Connect data from their Android device: daily metrics (steps, distance, calories, heart 
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
# Function Health (`function-health`)

> Retrieve lab biomarker results and clinician notes from Function Health.

## What is this?

The `function-health` skill is one of Muse's capabilities.

Official description: Retrieve lab biomarker results and clinician notes from Function Health.

## When to use?

When the user's request matches: Retrieve lab biomarker results and clinician notes from Function Health.

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: function-health
Purpose: Retrieve lab biomarker results and clinician notes from Function Health.
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
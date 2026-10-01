# Paired Devices (`paired-devices`)

> Manage the user's paired devices: list and describe devices, run commands on them, pull data such as location, and unpair devices.

## What is this?

The `paired-devices` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user mentions their phone or another paired device
- reading device location, or running a command on a device
- unpairing or troubleshooting a device

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: paired-devices
Purpose: Manage the user's paired devices: list and describe devices, run commands on them, pull data such as location, and unpai
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
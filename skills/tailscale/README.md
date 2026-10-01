# Tailscale (`tailscale`)

> Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and reach private machines through the TCP tunnel proxy. Read for Tailscale, VPN, MagicDNS, network egress, exit-node, or browser routing questions and supported limits.

## What is this?

The `tailscale` skill is one of Muse's capabilities.

Official description: Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and reach private machines through the TCP tunnel proxy. Read for Tailscale, VPN, MagicDNS, network egress, exit-node, or browser routing questions and supported limits.

## When to use?

When the user's request matches: Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and r

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: tailscale
Purpose: Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and reach private machine
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*
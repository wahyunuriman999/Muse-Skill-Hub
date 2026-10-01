# Connector Management (`connector-management`)

> Manage third-party service connectors: discover available connectors, check connection status and granted scopes, guide OAuth connect flows, and disconnect services.

## What is this?

The `connector-management` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- the user asks to connect, disconnect, or check a service (Gmail, Spotify, GitHub...)
- a skill fails because its service is not connected
- the user asks what accounts are linked

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: connector-management
Purpose: Manage third-party service connectors: discover available connectors, check connection status and granted scopes, guide 
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
# Secure Vault (`secure-vault`)

> Handle credentials securely: collect passwords, API keys, and tokens only through secure entry UI, never in chat; manage saved logins and one-time sign-in codes.

## What is this?

The `secure-vault` skill is one of Muse's platform capabilities — the product features around the assistant itself (settings, connections, devices, data), documented as a reusable pattern.

## When to use?

When the user's request matches:
- a service needs a password, API key, or token
- saving, replacing, or resetting a login
- a sign-in flow asks for a one-time/verification code

## General pattern

- **Check state before acting**: inspect connection, permission, or data status first — never assume.
- **Secure surfaces for secrets and money**: credentials and payments go through dedicated secure UI, never chat text.
- **Explicit approval for consequential actions**: deletions, purchases, outbound messages, and permission grants need a clear yes.

## Example adaptation pattern for other LLMs

```
Skill: secure-vault
Purpose: Handle credentials securely: collect passwords, API keys, and tokens only through secure entry UI, never in chat; manage
Input: clear user need + structured parameters
Output: verified result + its source
Rules: state-check first, secure UI for secrets/payments, approval for writes
```

---
*Platform capability pattern — documented so any LLM agent can implement an equivalent.*
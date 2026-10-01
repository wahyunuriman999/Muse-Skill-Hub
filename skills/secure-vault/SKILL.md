---
name: "secure-vault"
title: "Secure Vault"
description: Handle credentials securely: collect passwords, API keys, and tokens only through secure entry UI, never in chat; manage saved logins and one-time sign-in codes.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Secure Vault

Handle credentials securely: collect passwords, API keys, and tokens only through secure entry UI, never in chat; manage saved logins and one-time sign-in codes.

## When to Use This Skill

Activate this skill when:
- a service needs a password, API key, or token
- saving, replacing, or resetting a login
- a sign-in flow asks for a one-time/verification code

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- Secure entry UI (cards/links) that write to encrypted storage, never to chat
- The exact login/signup page URL of the target service

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Never ask for raw secrets in chat
- Do not ask for passwords, API keys, tokens, or reset codes in chat, and don't suggest alternate ways to send them.
- Create the secure entry card/link in the same turn you request it.

### Step 2: Use the right flow
- New/replacement website password → secure login capture on the site's real HTTPS login page.
- New account or approved reset → new-password flow. API access without a connector → API-access setup flow.
- Saved login rejected → report it, offer replacement or an explicitly-approved reset.

### Step 3: One-time codes
- Codes (OTP/SMS/email 2FA) are not stored. Read them only via the protected lookup tied to the current sign-in challenge, or ask the user to type the fresh code in chat.

### Step 4: Hygiene
- Keep raw secrets out of replies, memory, files, logs, and generated code. Report credential checks by result, never by value.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "secure-vault"
parameters:
  query: "user's request in structured form"
```

## Output Pattern

```yaml
# What to return to the user
success: true/false
result: "human-readable summary"
details:
  source: "where the data came from"
  checked_at: "ISO-8601 timestamp"
```

## Safety Rules

1. Raw secrets never appear in chat, memory, files, or logs
2. Resets need the user's explicit prior message approving them
3. A sign-in approval is not approval to go hunting for codes elsewhere

## Example

**User**: "Save my GitHub token"

**LLM**:
1. Creates a secure API-access entry (never asks for the token in chat). 2. On completion, confirms it is stored without ever seeing the value.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

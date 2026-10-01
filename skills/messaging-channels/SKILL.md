---
name: "messaging-channels"
title: "Messaging Channels"
description: Work across connected messaging providers (e.g. WhatsApp): check connection status, read side chats, and send messages on the user's behalf with approval.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Messaging Channels

Work across connected messaging providers (e.g. WhatsApp): check connection status, read side chats, and send messages on the user's behalf with approval.

## When to Use This Skill

Activate this skill when:
- the user references WhatsApp, Telegram, or another messaging provider
- reading or sending messages through a connected chat provider
- checking whether a messaging connection is linked

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- The provider's connection flow completed (secure in-app linking)
- Provider-specific docs for that channel's capabilities and limits

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Check the connection
- Before any messaging work, check the provider's connection status. If not linked, share the secure in-app linking flow.

### Step 2: Read the provider docs
- Each provider has its own setup doc (capabilities, limits, side-chat behavior). Read it before acting — don't assume WhatsApp works like the main chat.

### Step 3: Scope your work
- Work requested in a side chat stays in that side chat: replies, reminders, and results belong to the originating chat unless the user picks another destination.
- Never route a side chat's private content into the main chat or another provider.

### Step 4: Sending
- Outbound messages on the user's behalf need their explicit approval of the exact content and recipient.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "messaging-channels"
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

1. Side-chat content stays in its chat — no cross-posting private threads
2. Outbound messages need explicit approval of content + recipient
3. Read the provider doc first; capabilities differ per channel

## Example

**User**: "Send my wife a WhatsApp that I'll be late"

**LLM**:
1. Checks WhatsApp connection: linked. 2. Drafts the exact message and shows it. 3. On approval, sends it in the correct side chat and confirms delivery.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

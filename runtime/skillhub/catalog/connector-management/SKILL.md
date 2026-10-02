---
name: "connector-management"
title: "Connector Management"
description: Manage third-party service connectors: discover available connectors, check connection status and granted scopes, guide OAuth connect flows, and disconnect services.
version: "1.0.0"
license: "AGPL-3.0-only"
compatibility: "Any LLM with tool/function calling"
---

# Connector Management

Manage third-party service connectors: discover available connectors, check connection status and granted scopes, guide OAuth connect flows, and disconnect services.

## When to Use This Skill

Activate this skill when:
- the user asks to connect, disconnect, or check a service (Gmail, Spotify, GitHub...)
- a skill fails because its service is not connected
- the user asks what accounts are linked

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- A connector registry describing each service's OAuth flow, required scopes, and status check
- Ability to open the provider's official connect/authorization page

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Check status first
- Before promising work that needs a connected service, verify the connection (status check), not memory.
- Report the actual state: connected, expired, or never connected.

### Step 2: Connect flow
- Send the user through the service's real OAuth/authorization flow — never invent a settings page or pairing screen.
- After the flow, check status again before saying it is connected.

### Step 3: Scopes
- If an action needs a scope that was not granted, explain exactly which access is missing and link the scope-add flow.
- Never broaden a permission silently; the user approves each scope.

### Step 4: Disconnect
- Disconnect only on explicit user request; confirm which service is being disconnected.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "connector-management"
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

1. Never invent a connection flow, settings page, or pairing screen
2. Verify status before AND after connecting
3. Scope additions need their own explicit approval

## Example

**User**: "Connect my Spotify"

**LLM**:
1. Checks connector status: not connected. 2. Opens Spotify's official authorization page. 3. After return, re-checks status and confirms: connected.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*


## Actions

<!-- Auto-generated from the driver's ActionDef contracts
     (v2.1 doc-sync). Kept in sync by `skillhub validate`. -->

- **get_connector** — Get one connector's configuration.  
  Risk: `read` · parameters: provider · required: provider
- **list_connectors** — List connector configurations.  
  Risk: `read` · parameters: none · required: none
- **remove_connector** — Remove a connector configuration (needs confirm=true).  
  Risk: `account` · parameters: provider · required: provider
- **set_connector** — Add/update a connector configuration (needs confirm=true).  
  Risk: `write` · parameters: provider, auth_type, status, scopes · required: provider

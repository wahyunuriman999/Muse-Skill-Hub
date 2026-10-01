---
name: "paired-devices"
title: "Paired Devices"
description: Manage the user's paired devices: list and describe devices, run commands on them, pull data such as location, and unpair devices.
version: "1.0.0"
license: "MIT"
compatibility: "Any LLM with tool/function calling"
---

# Paired Devices

Manage the user's paired devices: list and describe devices, run commands on them, pull data such as location, and unpair devices.

## When to Use This Skill

Activate this skill when:
- the user mentions their phone or another paired device
- reading device location, or running a command on a device
- unpairing or troubleshooting a device

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- A device pairing registry with per-device capabilities
- Location/data access only with the user's permission for the task at hand

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Identify the device
- List paired devices and pick the right one; ask if ambiguous. Never assume which "my phone" is if several exist.

### Step 2: Least privilege
- Pull only the data the task needs (e.g. location for "where am I", not full device dump).
- If the device isn't sharing (location off, permission missing), say so plainly and explain how to enable it.

### Step 3: Commands
- Device commands (open URLs, trigger actions) need the user's explicit request for that command.

### Step 4: Unpair
- Unpair only on explicit request; confirm which device.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "paired-devices"
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

1. Pull minimum necessary data per task
2. Report disabled permissions honestly instead of guessing
3. Unpairing needs explicit confirmation of the exact device

## Example

**User**: "Where is my phone right now?"

**LLM**:
1. Lists paired devices, identifies the phone. 2. Reads its last shared location. 3. Reports the place and how fresh the reading is.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*

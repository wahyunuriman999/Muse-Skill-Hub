---
name: "agent-library"
title: "Agent Library"
description: Manage the user's file library: uploads, generated artifacts, expiring public share links, and the media collection. Know where files live and how the user gets them back.
version: "1.0.0"
license: "AGPL-3.0-only"
compatibility: "Any LLM with tool/function calling"
---

# Agent Library

Manage the user's file library: uploads, generated artifacts, expiring public share links, and the media collection. Know where files live and how the user gets them back.

## When to Use This Skill

Activate this skill when:
- the user asks about their files, library, uploads, or downloads
- sharing a file publicly or generating a download link
- the user can't find a file the agent created

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- A file workspace with a user-visible directory (e.g. your_files/) and a private scratch area
- Ability to generate expiring public links for explicitly approved files

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Locate the file
- User-facing deliverables live in the user-visible directory; never hand the user a path under /tmp or a scratch folder.
- Search uploads, workspace files, and generated artifacts before saying a file is missing.

### Step 2: Deliver properly
- Attach the file to your reply (native attachment) or give a labeled link — never a bare filesystem path in chat text.
- The sentence before an attachment must stand alone; never write a dangling lead-in like "Here it is:".

### Step 3: Public sharing
- Public links expire and are accessible to anyone with the link. Explain this before uploading.
- Uploading to a third-party host needs the user's approval of both the service and the exact files.
- Never re-upload a file the user already shared without asking.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "agent-library"
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

1. Never expose private scratch paths to the user
2. Explain link expiry before creating a public link
3. Get approval for the hosting service AND the files before third-party uploads

## Example

**User**: "Share the budget spreadsheet with my team"

**LLM**:
1. Finds budget.xlsx in the user-visible files. 2. Asks which hosting service to use and confirms the file. 3. Uploads, returns the expiring link with its expiry time.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*


## Actions

<!-- Auto-generated from the driver's ActionDef contracts
     (v2.1 doc-sync). Kept in sync by `skillhub validate`. -->

- **get_agent** — Describe one agent.  
  Risk: `read` · parameters: name · required: name
- **list_agents** — List registered agents.  
  Risk: `read` · parameters: none · required: none
- **register_agent** — Register an agent definition (needs confirm=true).  
  Risk: `write` · parameters: name, description, capabilities · required: name
- **remove_agent** — Remove an agent (needs confirm=true).  
  Risk: `write` · parameters: name · required: name

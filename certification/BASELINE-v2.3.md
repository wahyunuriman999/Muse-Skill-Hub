# GATE 0 — v2.3.0 Certification Baseline & Recovery Record

This file is the immutable starting point of the v2.3.0 certification.
Every later gate builds on this exact base. If the working tree is ever
lost, re-clone and verify you land here before continuing.

`main` is FROZEN at certified v2.2.1 (`e778397`) and is not touched by
this certification. No merge, no tag, no release — certification only.

## Source of truth (verified 2026-10-04)

| Item | Value |
|---|---|
| `git rev-parse HEAD` | `bd45788ab5a55d8fde40a097651f46aef8ead986` |
| `git rev-parse origin/v2.3.0-dev` | `bd45788ab5a55d8fde40a097651f46aef8ead986` |
| `git ls-remote origin refs/heads/v2.3.0-dev` | `bd45788ab5a55d8fde40a097651f46aef8ead986` |
| Working branch | `v2.3.0-dev` (branched from v2.2.1 `e778397`) |
| `main` | untouched at `e778397` (certified v2.2.1) |

Mismatch policy: if any of the three SHAs disagree, STOP. Do not build
certification on a wrong base.

## What v2.3.0-dev changes vs certified v2.2.1

1. `lovable` and `replit` upgraded from honest stubs to real API drivers
   (Lovable `https://api.lovable.dev/v1`, plan-gated; Replit Admin API
   `https://api.replit.com`, Enterprise-gated). Only `muse-early-access`
   remains an honest stub.
2. New write-ahead log `runtime/skillhub/wal.py` + `skillhub idempotency
   recover` CLI: stale PENDING keys are classified as `safe_to_reclaim`
   / `needs_reconciliation` / `in_flight` instead of all being manual
   mysteries. Exactly-once across arbitrary external APIs remains
   honestly impossible; uncertain post-call crashes are never auto-retried.
3. Live contract harness `runtime/tools/live_contracts.py` (63 read-only
   specs).
4. PyPI/MCP prep: version `2.3.0.dev0`, SPDX `AGPL-3.0-only`, LICENSE in
   wheel+sdist, console alias `muse-skill-hub-runtime`, `visibility/server.json`.

## Platform baseline

| Item | Value |
|---|---|
| OS | Linux `7.0.0-39-generic` x86_64 |
| Python | 3.12.3 |
| build | 1.6.1 |
| cryptography | 50.0.2 |
| httpx | 0.28.1 |
| jsonschema | 4.26.0 |
| mcp | 1.30.0 |
| PyYAML | 6.0.3 |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 |
| twine | 7.0.0 |

## Catalog baseline (v2.3.0-dev)

- skills: **97**, implemented: **96**, honest stubs: **1** (`muse-early-access`)
- MCP tools: **221**

## Test baseline

- Full suite: **301 passed** (see `runtime/tests/`, Linux, Python 3.12.3)
- Conformance validator: **PASS (0 warnings)** (re-verified per gate)

## Recovery procedure

```bash
git clone https://github.com/wahyunuriman999/Muse-Skill-Hub.git ~/workspace/muse-skill-hub
cd ~/workspace/muse-skill-hub
git fetch --all --tags --prune
git checkout v2.3.0-dev
git rev-parse HEAD   # must equal bd45788... until GATE checkpoints advance it
```

Then continue from the latest pushed GATE checkpoint commit on
`origin/v2.3.0-dev` — never from `/tmp`, venvs, or memory.

# GATE 0 — Certification Baseline & Recovery Record

> **Date correction (2026-10-02):** this file states "verified 2026-10-02",
> but the baseline verification it records was actually performed on
> **2026-10-01** (system/work date); the file was written with the wrong
> date. The verified values themselves (SHAs, tag, release) are unaffected
> and remain correct. This note corrects the record without rewriting
> history.

This file is the immutable starting point of the v2.2.x final certification.
Every later gate builds on this exact base. If the working tree is ever lost,
re-clone and verify you land here before continuing.

## Source of truth (verified 2026-10-02)

| Item | Value |
|---|---|
| `git rev-parse HEAD` | `f72a7e3ec3d1df510931ab263bcf9731b101040c` |
| `git rev-parse origin/main` | `f72a7e3ec3d1df510931ab263bcf9731b101040c` |
| `git ls-remote origin refs/heads/main` | `f72a7e3ec3d1df510931ab263bcf9731b101040c` |
| tag `v2.2.0` | `f72a7e3ec3d1df510931ab263bcf9731b101040c` |
| GitHub latest release | v2.2.0 (`f72a7e3`) — confirmed on release page |
| Working branch | `final-certification` (branched from `f72a7e3`) |
| `main` | untouched at `f72a7e3` — practical immutable baseline |

Mismatch policy: if any of the three SHAs disagree, or `v2.2.0` does not
point at `f72a7e3`, STOP. Do not build certification on a wrong base.

## Platform baseline

| Item | Value |
|---|---|
| OS | Linux `7.0.0-39-generic` x86_64 |
| Python | 3.12.3 |
| cryptography | 50.0.2 |
| httpx | 0.28.1 |
| jsonschema | 4.26.0 |
| mcp | 1.30.0 |
| PyYAML | 6.0.3 |
| pytest / pytest-asyncio | 9.1.1 / 1.4.0 |

## Catalog baseline (v2.2.0)

- skills: **97**, implemented: **94**, honest stubs: **3** (`lovable`, `muse-early-access`, `replit`)
- MCP tools: **210**

## Test baseline

- Full suite: **109 passed** (see `runtime/tests/`)
- Conformance validator: **PASS (0 warnings)**

## Recovery procedure

```bash
git clone https://github.com/wahyunuriman999/Muse-Skill-Hub.git ~/workspace/muse-skill-hub
cd ~/workspace/muse-skill-hub
git fetch --all --tags --prune
git checkout final-certification
git rev-parse HEAD   # must equal f72a7e3... until GATE checkpoints advance it
```

Then continue from the latest pushed GATE checkpoint commit on
`origin/final-certification` — never from `/tmp`, venvs, or memory.

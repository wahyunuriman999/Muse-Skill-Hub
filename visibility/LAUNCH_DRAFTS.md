# Launch Drafts — Muse Skill Hub v2.2.1

Copy-paste ready drafts. Repo: https://github.com/wahyunuriman999/Muse-Skill-Hub
Author: Wahyu Nur Iman. License: AGPL-3.0.

Tone rule for all of these: honest engineering. The differentiator is the
rigorous certification process, not marketing. No inflated claims.

---

## 1. Reddit r/mcp (technical, Show-and-tell)

**Title:** Show-and-tell: Muse Skill Hub — 97 skills as typed, permission-enforced MCP tools, with a 23-gate certification process

**Body:**

Hi r/mcp — I built an open-source runtime that turns 97 capabilities (Gmail, GitHub, Spotify, spreadsheets, scheduling, etc.) into typed MCP tools with permission enforcement at dispatch time. Define a capability once, discover it dynamically, execute it through tools with input/output schema validation. It's LLM-agnostic: anything with tool/function calling can use it.

What I think is actually interesting about this project isn't the skill count — it's the certification process it went through:

- **23/23 gates, 0 blockers, verdict PASS** — each gate is an atomic checkpoint (test → commit → push → verify remote SHA), documented with commit evidence in `certification/`.
- **271 automated tests green**, including 20-process race tests for atomic approval consumption and idempotency reservation, and crash-atomic storage tests.
- **CI 12/12 green on Ubuntu/Windows/macOS × Python 3.10–3.13**, with genuine `windows-latest` execution — the msvcrt lock path and spawn-based process races actually ran on Windows runners.
- The CI caught **3 real defects** no Linux run could see: a missing `build` test dependency, a hardcoded unix platform assertion, a Python 3.10 `tomllib` gap, and a Windows `EDEADLK` file-lock race under contention. All fixed with bounded backoff + regression tests, then re-verified. That's how certification should work: test → fail → find real bug → fix → PASS.
- **Byte-reproducible wheel** built from a clean checkout; validator passes against a fresh install.

Honest scope, because this matters: it's a **trusted local single-user MCP runtime** — not multi-user SaaS, no tenant isolation, no distributed exactly-once. The threat model explicitly admits that a crash after a provider side effect but before the local idempotency commit can still duplicate the side effect. Provider drivers: 2 live-tested against real servers (GitHub, podcast), 1 mock-contract (Stripe), 91 structural.

AGPL-3.0. Feedback and teardown welcome — the certification docs are all in the repo.

https://github.com/wahyunuriman999/Muse-Skill-Hub

---

## 2. Reddit r/LocalLLaMA (local-first / privacy angle)

**Title:** I built a local-first skill runtime for AI agents — 97 capabilities as MCP tools, everything stays on your machine

**Body:**

If you run local models and want them to *do* things (Gmail, GitHub, files, spreadsheets, scheduling) without shipping your data to someone else's cloud, this might be useful: Muse Skill Hub.

The whole design is local-first and single-user by construction:

- Runs entirely on your machine as an MCP server. No accounts, no telemetry, no cloud backend.
- Credentials live in a local encrypted store (Fernet, same key machinery as the built-in secure vault) — plaintext fallback was removed, legacy files get migrated and deleted.
- Permission enforcement at dispatch: actions declare risk levels, destructive ones need explicit approval, and approvals are consumed atomically (race-tested with 20 parallel processes).
- Tamper-evident audit log (hash-chained) so you can verify what the agent actually did.
- Works with any LLM that supports tool/function calling — including local ones.

It went through a fairly serious certification: 23/23 gates PASS, 271 tests, CI green on Windows/Linux/macOS × Python 3.10–3.13. The threat model is explicit about the boundary: trusted, local, single-user, one machine, one LLM client. It deliberately does *not* claim to be multi-user SaaS or to solve distributed exactly-once — those are out of scope, stated upfront.

Honest caveat: of 97 skill drivers, 2 are live-tested against real provider APIs, 1 has a mock-contract test, and 91 are structural (real code, but you'll need your own API keys — the repo can't and won't ship credentials).

AGPL-3.0, by Wahyu Nur Iman.

https://github.com/wahyunuriman999/Muse-Skill-Hub

---

## 3. Hacker News — Show HN

**Title:** Show HN: Muse Skill Hub – 97 skills as typed, permission-enforced MCP tools

**Body:**

Muse Skill Hub is an open-source, LLM-agnostic capability runtime: 97 skills (Gmail, GitHub, Spotify, spreadsheets, etc.) exposed as typed MCP tools with permission enforcement at dispatch.

What/why/how:

- **What:** define a capability once (SKILL.md + driver + JSON schemas), discover it dynamically via TF-IDF search, execute it through strictly-validated tools. Strict schema validation by default (unknown params rejected, like MCP's additionalProperties: false).
- **Why:** I wanted a skill system where the safety properties are enforced by the runtime, not hoped for in prompts — atomic approval consumption, idempotency reservation before side effects, crash-atomic local storage, scope-bound credentials.
- **How it was verified:** a 23-gate certification process, each gate an atomic checkpoint with commit evidence. 271 tests green. CI 12/12 on Ubuntu/Windows/macOS × Python 3.10–3.13 with real Windows runners — which caught 3 genuine defects invisible on Linux, including a Windows EDEADLK lock race under 20-process contention (fixed with bounded backoff + regression tests). Byte-reproducible wheel, fresh-install validation.

Deliberately honest scope: trusted local single-user runtime. The threat model states its limits plainly, including that a crash between a provider side effect and the local idempotency commit can duplicate the effect. No multi-user SaaS claims.

AGPL-3.0. https://github.com/wahyunuriman999/Muse-Skill-Hub

Happy to answer technical questions — the full certification trail is in certification/.

---

## 4. X / Twitter (single post, under 280 chars)

Shipped: Muse Skill Hub v2.2.1 — 97 skills as typed, permission-enforced MCP tools for any LLM. 23/23 certification gates PASS, 271 tests, CI green on Win/Linux/macOS. Honest scope: local single-user runtime. AGPL-3.0.
https://github.com/wahyunuriman999/Muse-Skill-Hub

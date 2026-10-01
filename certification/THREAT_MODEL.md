# Muse Skill Hub — Threat Model

_Companion to the final certification (GATE 19). This document states what the
runtime protects, from whom, how, and — just as importantly — what it does
**not** promise. Every mitigation names the gate that proves it._

## 1. System shape

Muse Skill Hub is a **trusted local single-user MCP runtime**. One operator, one
machine, one LLM client. It is not a multi-user service, not a SaaS backend, and
not distributed infrastructure. All security reasoning below assumes this shape;
deploying it as anything else invalidates the model.

```
 ┌──────────┐   MCP tools    ┌─────────────────────┐   HTTPS    ┌───────────┐
 │   LLM    │ ◄────────────► │  skillhub runtime   │ ◄────────► │ providers │
 │(untrusted│   (no raw      │  (this repo)        │  (untrusted│ (GitHub,  │
 │ for      │   secrets ever │                     │   input)   │  Stripe…) │
 │ secrets) │   cross this)  └─────────────────────┘            └───────────┘
 └──────────┘           │                    │
                        │ files              │ files
                        ▼                    ▼
              ┌──────────────────┐  ┌──────────────────┐
              │ credential store │  │ approvals/audit/ │
              │ (encrypted)      │  │ idempotency      │
              └──────────────────┘  └──────────────────┘
                    local machine — single-user trust boundary
```

## 2. Assets

| Asset | Where | Sensitivity |
|---|---|---|
| Provider credentials (API keys, tokens) | `credentials.enc` (AES-256-GCM via `cryptography`), env vars, OS keyring | **Critical** — long-lived, provider-wide |
| Approval records (intent to act) | `approvals.json` | High — authorizes side effects |
| Audit log (hash-chained JSONL) | `audit.jsonl` | High — tamper-evidence, operator forensics |
| Idempotency store | `idempotency.json` | Medium — replays, result snapshots |
| OAuth tokens | credential store | Critical — same as credentials |
| User data in transit (params, results) | memory, logs | Medium — redacted at rest |

## 3. Trust boundaries

1. **The LLM is untrusted for secrets.** It never receives a raw credential:
   drivers get a `credential_ref`, headers are built inside the runtime, and
   error `internal` detail is stripped unless the operator enables debug mode.
   (GATE 1, GATE 6, GATE 16)
2. **Providers are untrusted input.** Responses are parsed against declared
   output schemas; malformed bodies become `{"raw": ...}`, never executed.
   (GATE 7, GATE 14)
3. **The local machine is trusted (single user).** Apart from the encrypted
   credential store, local files are plaintext inside the operator's account.
   A second local user, or malware on the box, is outside the model.
4. **The operator is trusted.** Approval decisions, debug mode, key release
   after a crash, and volume encryption are the operator's responsibility.
5. **The network between runtime and provider is TLS** (via `httpx` defaults);
   the runtime does not implement its own transport security.

## 4. Threats and mitigations

| # | Threat | Mitigation | Gate |
|---|---|---|---|
| T1 | LLM exfiltrates a credential via tool output, error message, or approval preview | Credentials resolve to references; `to_dict()`/`to_envelope()` strip `internal`; approval/audit/idempotency stores keep `params_hash` + redacted preview only; secret-shaped values scrubbed recursively; canary tests across exceptions, approval, audit, idempotency, CLI, MCP | 1, 6, 16 |
| T2 | Credential from source A is scope-checked against source B (confused deputy) | Credential resolution and scope verification happen on ONE `CredentialResolution` object per flow; exploit test fails | 1 |
| T3 | Two processes approve/consume the same approval, or double-execute under one idempotency key | File-locked critical sections; atomic consume; atomic PENDING reservation before side effects; 20-process race tests | 3, 4, 5 |
| T4 | Crash between writes corrupts approvals/audit/idempotency | Separate `.lock` files, tmp+fsync+`os.replace`, torn-tail repair on audit log; torn writes can never half-commit | 3 |
| T5 | Retry duplicates a provider side effect (e.g. double charge) | 5xx retried for safe methods only; mutations never retried; 429 honored with `Retry-After`; mutation 5xx raises `UpstreamUnavailable` after one attempt | 14 |
| T6 | Tampered audit log (edit/delete/reorder) goes unnoticed | Hash-chained JSONL; `audit-verify` detects tampering | v2.1, 16 |
| T7 | A driver silently downgrades its risk or smuggles an undocumented action | Validator fails on manifest/driver/SKILL drift, undocumented actions, and risk downgrades (4 actions conformance-bumped to `destructive`) | 8, 9 |
| T8 | Malicious dependency ships a CVE | `pip check` clean; `pip-audit` (OSV) 0 vulns across 63 packages; findings attributed per group (project/test/toolchain) | 17 |
| T9 | Provider returns attacker-controlled data that breaks parsing or leaks through errors | Output-schema enforcement; malformed bodies → `{"raw"}`; error `internal` scrubbed before audit logging | 7, 14, 16 |
| T10 | Stale OAuth token reused / concurrent refresh storms | Single-flight refresh under the store lock; double-checked expiry; 20-thread test → exactly 1 refresh | v2.2 |
| T11 | Corrupt credential store silently yields "no credentials" | Fail-closed: `CredentialStoreCorruptError` + backup, never an empty store masquerading as "no credentials" | v2.2 |
| T12 | Windows behaves differently (locks, spawn, paths) | Cross-platform `filelock` (fcntl/msvcrt), no top-level `fcntl` import; real `windows-latest` CI | 2, 20 |

## 5. Accepted limitations (explicitly NOT promised)

These are honest boundaries of a local-file runtime. They are documented here
so no claim elsewhere can be read as contradicting them.

- **L1 — Crash after external side effect, before idempotency commit.**
  If the provider executes the side effect and the process dies before the
  local SUCCEEDED commit, a retry may repeat the side effect. The local
  runtime cannot close this window; providers with their own idempotency
  keys are the real fix. (Documented in `_idem_reserve` and GATE 4.)
- **L2 — Single user, single machine.** No tenant isolation, no multi-user
  access control, no protection against another local user or malware on the
  same box. Volume encryption is the operator's job.
- **L3 — Audit log is tamper-evident, not tamper-proof.** The hash chain
  *detects* edits; a filesystem-level attacker can still rewrite the whole
  file. For stronger guarantees, ship the log to a WORM / remote append-only
  store.
- **L4 — Local stores other than the credential vault are plaintext.**
  Approvals, audit, and idempotency files live in the operator's local dir
  unencrypted (inside the single-user trust boundary, §3.3).
- **L5 — Provider coverage is honest, not complete.** 2 of 94 drivers are
  live-tested against real provider servers (`github`, `podcast`), 1 has a
  mock-harness contract test (`stripe`), 91 are structural. See
  `PROVIDER_MATRIX.md`. (GATE 15)
- **L6 — No distributed guarantees.** Exactly-once execution, distributed
  OAuth locking, and cross-machine coordination are not claimed and not
  attempted.
- **L7 — `internal` error detail is debug-only.** With `SKILLHUB_DEBUG=1` the
  operator explicitly opts into seeing provider internals; that mode is not
  for shared/log-shipped operation.
- **L8 — Supply chain is point-in-time.** The GATE 17 audit (0 vulns) covers
  the scanned dependency set on the scan date; re-run before every release.

## 6. What would change the model

- Multi-user or network-exposed deployment → requires authentication,
  authorization, tenant isolation, and encrypted-everything: a different
  product, not a harder gate.
- Handling payment-card or health data at rest → encrypt the idempotency and
  audit stores, not just credentials.
- Shared/forwarded audit logs → remote append-only sink (L3).

_This model is part of the certification freeze: changes to trust boundaries
require a new certification pass, not a patch release._

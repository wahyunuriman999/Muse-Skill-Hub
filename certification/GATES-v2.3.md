# Certification Ledger — v2.3.0 re-certification

_Each gate is atomic: verify → fix/new tests if needed → commit → push →
triple-verify (`HEAD == origin/v2.3.0-dev == ls-remote`) → clean tree →
next gate. Test counts do not define certification; each gate's tests
target its specific guarantee. `main` stays frozen at certified v2.2.1;
no merge, no tag, no release — certification only._

Baseline: `bd45788` (GATE 0). Branch: `v2.3.0-dev`.

| Gate | Name | Commit | Status |
|---|---|---|---|
| 0 | Baseline & Recovery (v2.3) | `1febbc8` | COMPLETE |
| 1 | Credential Source/Scope Binding | `—` | COMPLETE (17 tests) |
| 2 | Windows Real Execution | — | PENDING |
| 3 | Crash-Atomic Storage | — | PENDING |
| 4 | Idempotency Semantics (+ WAL) | — | PENDING |
| 5 | Approval Protocol | — | PENDING |
| 6 | Approval Data Privacy | — | PENDING |
| 7 | Output Contract | — | PENDING |
| 8 | Risk Semantics | — | PENDING |
| 9 | Manifest/Driver/SKILL Contract | — | PENDING |
| 10 | MCP Documentation Consistency | — | PENDING |
| 11 | Generated Documentation | — | PENDING |
| 12 | Clean Installation | — | PENDING |
| 13 | Static Security Audit | — | PENDING |
| 14 | HTTP Safety | — | PENDING |
| 15 | Provider Contract Matrix (+ lovable/replit real) | — | PENDING |
| 16 | Exception & Secret Leak Assurance | — | PENDING |
| 17 | Dependency/Supply Chain | — | PENDING |
| 18 | Performance Sanity | — | PENDING |
| 19 | Threat Model (+ WAL surface) | — | PENDING |
| 20 | Cross-Platform CI (12/12) | — | PENDING |
| 21 | Release Reproducibility | — | PENDING |
| 22 | Final Certification Report | — | PENDING |
| 23 | WAL Crash Recovery (kill -9 at each phase) | — | PENDING |
| 24 | Lovable/Replit Real Drivers | — | PENDING |
| 25 | Live Contract Harness | — | PENDING |
| 26 | PyPI/MCP Packaging | — | PENDING |

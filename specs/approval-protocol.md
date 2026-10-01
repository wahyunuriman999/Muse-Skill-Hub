# Approval protocol (v2)

Replaces the bare `confirm=true` boolean for anything riskier than a plain
write.

```
LLM                    runtime                  human
 │                        │                        │
 │  action(params)        │                        │
 ├───────────────────────►│                        │
 │                        │ policy: approval_required
 │  ◄─────────────────────┤
 │  approval_required     │ creates apr_… (pending,
 │  approval_id=apr_…     │ bound to skill/action/
 │                        │ params hash, TTL 600s)
 │                        │                        │
 │                        │   approve / deny       │
 │                        │ ◄──────────────────────┤
 │                        │                        │
 │  action(params,        │                        │
 │    approval_id=apr_…)  │                        │
 ├───────────────────────►│ validates:             │
 │                        │  • exists & approved   │
 │                        │  • not expired         │
 │                        │  • not consumed before │
 │                        │  • same skill/action   │
 │                        │  • same params hash    │
 │                        │  • same actor (session │
 │                        │    label bound at      │
 │                        │    request time)       │
 │                        │ executes (single-use)  │
 │  ◄─────────────────────┤                        │
 │  result                │ audit-logged           │
```

Legacy `confirm=true` still works for `risk=write` actions. For
`sensitive`, `destructive`, `communication`, `financial`, `account`,
`device` the runtime refuses bare confirmation and mints a pending
approval instead.

The `permission-model` skill (`request_approval`, `list_pending`,
`approve`, `deny`) is the user-facing surface of this engine — one
system, not two.

## Concurrency (v2.1)

The `approved → consumed` transition happens inside one locked
read-modify-write critical section (`localstore.locked_json`), so two
workers racing on the same approval id get exactly one winner — the other
sees `approval_revoked`. The `actor` label is bound at request time and
checked at consumption; it is a local session label, not cryptographic
authentication. This remains a trusted single-user local boundary, not a
multi-user identity system.

## Idempotency states (v2.1)

Reservation is atomic and happens *before* side effects:
`PENDING → SUCCEEDED | FAILED → CONFLICT`. A concurrent duplicate sees
`pending` and does not re-execute; a mismatched call on the same key raises
`idempotency_conflict`; a failed record may be reclaimed exactly once for a
retry.

The field is `supports_idempotency_key` (renamed from `idempotent` in
v2.1): it means "the runtime may deduplicate with a key", not "the
underlying operation is mathematically idempotent".

## Storage privacy (v2.2)

The approval store keeps `params_hash` (sha256, the binding) plus a
redacted `params_preview` — never the raw params. Secret-looking keys
(password/token/secret/…) are stored as `[redacted]`, other values are
truncated, following the same policy as the audit log. Execution
re-supplies the real params; `consume()` verifies them against the hash.

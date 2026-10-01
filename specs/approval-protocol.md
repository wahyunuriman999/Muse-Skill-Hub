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

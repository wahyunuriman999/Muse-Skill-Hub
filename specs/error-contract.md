# Error contract (v2)

Every failure surfaces as this envelope to the LLM:

```json
{
  "ok": false,
  "error": {"code": "RATE_LIMITED", "message": "…", "retryable": true, "retry_after": 30},
  "meta": {"request_id": "9f2c41ab", "skill": "gmail", "action": "send_message"}
}
```

## Codes

| code | meaning | retryable |
|---|---|---|
| `invalid_input` | params failed schema validation | no |
| `auth_required` | credentials missing | no |
| `auth_expired` | 401/403 from upstream | no |
| `permission_denied` | not allowed at all | no |
| `policy_blocked` | denied by policy engine | no |
| `approval_required` | needs approval_id (or confirm=true for plain writes) | no |
| `approval_expired` | approval TTL passed | no |
| `approval_revoked` | denied, consumed, or params mismatch | no |
| `rate_limited` | HTTP 429, `retry_after` set | yes |
| `not_found` | HTTP 404 | no |
| `conflict` | HTTP 409 | no |
| `upstream_unavailable` | HTTP 5xx | yes |
| `timeout` | upstream timeout | yes |
| `upstream_error` | other upstream failure | yes |
| `idempotency_conflict` | key reused for a different call | no |
| `driver_not_implemented` | catalog-only stub | no |
| `internal_error` | runtime bug / corrupt store | no |

## Security rule

`message` is always safe for the LLM. Internal details (tracebacks,
provider payloads, secret values) go to the audit log only. Set
`SKILLHUB_DEBUG=1` to include internals during development.

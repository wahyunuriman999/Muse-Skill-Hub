# v2.1 migration notes

v2.1.0 hardens the v2.0 execution core. It is backward compatible for
normal use; the notes below cover the breaking-ish edges.

## Renamed: `idempotent` → `supports_idempotency_key`

`ActionDef(idempotent=...)` still works but is deprecated; the canonical
field is `supports_idempotency_key`. Manifests now emit
`supports_idempotency_key` (and a new `required_scopes` list per action).
Regenerate manifests with `python tools/generate_manifests.py`.

The rename is semantic, not cosmetic: the flag means "the runtime may
deduplicate this action with an idempotency key", not "the underlying
operation is mathematically idempotent".

## Credentials: plaintext fallback removed

Local credentials now live in encrypted `credentials.enc` (Fernet, keyed
from the secure-vault machinery). On first use, an existing plaintext
`credentials.json` is migrated into the encrypted store and **deleted**.
External secret managers and env injection remain preferable for hostile
environments — the encryption protects against casual disk/backup
exposure, not against malware or a same-user attacker.

## Stricter validation

- `ActionDef.strict` defaults to `True`: unknown parameters are rejected
  (MCP-style `additionalProperties: false`).
- Input validation now enforces the full JSON-Schema-like keyword set
  (`pattern`, `format`, `oneOf`, nested `properties`, etc.). Schemas that
  were loose before may now reject inputs they used to accept.
- Handler results are validated against `output_schema` before success is
  committed. Actions with empty `{}` output schemas are unaffected.

## Approval actor binding

`request_approval(..., actor="...")` binds a session label; `consume`
rejects a different actor with `approval_revoked`. Callers that never
passed `actor` are unaffected (both sides default to the same label).

## Scope enforcement

Actions may declare `required_scopes`. When the stored credential carries
scope metadata, a mismatch raises `scope_mismatch`. Plain environment
tokens (scopes unknown) are allowed but audited as `unverified` — this is
local-runtime compatibility, not strict enterprise OAuth enforcement.

## New dependency

`pyyaml>=6.0` (manifest risk is now read from `manifest.yaml` at registry
load; the central `RISK_OVERRIDES` table is gone).

## New CLI

- `python -m skillhub.cli audit-verify` — verifies the tamper-evident
  audit hash chain.

## Test count

67 → 91 tests, including 20-thread concurrency races for approval
consumption and idempotency reservation.

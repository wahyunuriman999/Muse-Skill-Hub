# v2.2 migration notes

v2.2.0 hardens concurrency and crash safety across the v2.1 execution
core. It is backward compatible for normal use; the notes below cover
the edges worth knowing.

## Cross-platform file locking

`skillhub/filelock.py` is the single locking primitive now (`fcntl` on
Unix, `msvcrt` on Windows). There is no top-level `import fcntl` left in
the runtime, so the package imports cleanly on Windows. Lock files are
separate `<name>.lock` files — never the data file itself.

## Crash-atomic stores

`localstore.locked_json()` and the credential store now write via
tmp + fsync + `os.replace` under a separate lock file: atomic against
concurrency *and* crashes. A crash mid-write leaves the old file or the
new file, never a truncated one.

## Credential store is fail-closed

A present-but-undecryptable `credentials.enc` now raises
`CredentialStoreCorruptError` (code `internal_error`, with a
`.corrupt.<timestamp>.enc` backup) instead of silently behaving as
"no credentials". Missing file still means empty.

## OAuth refresh is single-flight

`oauth.get_valid_token()` holds the credential store lock for the whole
check → refresh → persist cycle and re-checks expiry after acquiring it.
Concurrent workers racing an expired token produce exactly one refresh
request; the losers reuse the winner's rotated token. The network call
happens under the lock — deliberate, because with refresh-token rotation
two concurrent refreshes could invalidate each other.

## Approval store no longer keeps raw params

Stored approvals keep `params_hash` plus a redacted `params_preview`
(secret keys → `[redacted]`, other values truncated — the audit log's
policy). Execution re-supplies the real params; `consume()` verifies
them against the hash. If you read `approvals.json` directly, the
`"params"` key is gone.

## Real JSON Schema (Draft 2020-12)

`skillhub/validate.py` now runs on the standard `jsonschema` library —
the full vocabulary (`$ref`/`$defs`, `if`/`then`/`else`,
`dependentRequired`, `contains`, `propertyNames`, …) with format
checking. Actions may declare `$defs` alongside parameters for `$ref`
use. `skillhub validate` lints every action's input/output schema.

New declared dependencies: `cryptography>=41`, `jsonschema>=4.18`
(they were already required at runtime; now they're official).

## Destructive actions need approval

`skillhub validate` now fails when an action with a destructive name
(`delete_*`, `remove_*`, `destroy`, `revoke`, `terminate`, `purge`,
`wipe`) carries plain `risk: write` (bare `confirm=true`). Four actions
were bumped to `risk: destructive` (approval-gated):
`agent-library.remove_agent`, `device-data.delete_local_copy`,
`outlook-calendar.delete_event`, `secure-vault.delete_secret`.

## Manifest generator preserves hand-tuned risks

The manifest is the canonical risk source and may be hand-tuned.
`tools/generate_manifests.py` now only overwrites a manifest risk when
the driver declares an explicit `ActionDef(risk=...)` (tracked via
`ActionDef.risk_explicit`); otherwise the existing manifest risk is kept.

## Generated README metrics

`runtime/tools/sync_readme.py` regenerates the README metrics block from
the registry + test suite. A test (`test_readme_metrics_in_sync`) fails
if the README drifts — run the script before committing.

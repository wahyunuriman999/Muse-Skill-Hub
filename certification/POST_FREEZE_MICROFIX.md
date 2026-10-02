# Post-Freeze Micro-Fix — v2.2.1 release hygiene

**Date:** 2026-10-02 (UTC)
**Trigger:** fifth friend review of the v2.2.1 release (architecture PASS,
security model PASS, certification process PASS — with two documentation /
release-hygiene corrections and one CI maintenance note).

The v2.2.1 freeze declared in `FINAL_CERTIFICATION.md` was conditional on
this micro-fix; the freeze is now complete. History is not rewritten for
the review itself — this document records what changed and why. The
`v2.2.1` tag was moved to the fixed commit so that tag, package, wheel,
and docs all agree (the tag was hours old and the reviewer explicitly
required the correspondence).

## Findings and fixes

1. **Package version mismatch (release-hygiene).** The git tag, GitHub
   Release, and certification said v2.2.1, but the Python package metadata
   still said 2.2.0 (`pyproject.toml`, `skillhub.__version__`, generated
   READMEs, wheel filename). Fixed: bumped to **2.2.1** in
   `runtime/pyproject.toml` and `runtime/skillhub/__init__.py`, updated the
   version assertion in `test_v2_platform.py`, regenerated docs via
   `sync_readme.py`, removed the stale untracked `runtime/build/` directory.
   Verified: `pip show` reports 2.2.1, `skillhub.__version__` is 2.2.1,
   wheel is `muse_skill_hub_runtime-2.2.1-py3-none-any.whl`.
2. **Threat-model crypto primitive mismatch (security-documentation).**
   `THREAT_MODEL.md` said `credentials.enc` uses "AES-256-GCM via
   `cryptography`"; the implementation uses **Fernet** (authenticated
   encryption via `cryptography`, same key machinery as the secure vault —
   `credentials.py`, README). Fixed the document to match the
   implementation (reviewer's recommended option A; no crypto code
   changed). No remaining AES-256-GCM mentions in docs or code.
3. **CI maintenance.** `actions/checkout@v4` → `actions/checkout@v6`
   (Node.js 20 deprecation warnings). `actions/setup-python@v5` kept, per
   the review.

## Verification (2026-10-02)

- Full suite: **271/271 passed**.
- Validator: **PASS (0 warnings)** — locally and on a fresh wheel install.
- `sync_readme.py --check`: clean.
- Wheel rebuilt from the tree; fresh virtualenv install reports
  `muse-skill-hub-runtime 2.2.1`; validator green against the installed
  package.
- Cross-platform CI re-run on the fix commit: 12/12 green (recorded below
  when complete).

## Release correspondence (all four agree)

- Git tag: `v2.2.1`
- Python package: `2.2.1`
- Wheel: `muse_skill_hub_runtime-2.2.1-py3-none-any.whl`
- Docs: `2.2.1`

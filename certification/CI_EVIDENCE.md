# CI Evidence — GATE 20 (also repairs GATE 2)

## Workflow

- File: `.github/workflows/ci.yml` (committed via git after the `gh` OAuth
  token was re-authorized with the `workflow` scope through the device flow
  on 2026-10-02 — earlier pushes of this path were rejected by GitHub).
- Workflow name: `certification`.
- Triggers: push to `main` / `final-certification`, pull requests to `main`,
  manual `workflow_dispatch`.
- Matrix: `ubuntu-latest` + `windows-latest` + `macos-latest` ×
  Python 3.10 / 3.11 / 3.12 / 3.13 (12 jobs, `fail-fast: false`).
- Each job runs: `pip install -e "./runtime[test]"` → `python -m
  skillhub.cli validate` (0 warnings required) → `python -m pytest
  runtime/tests/ -q -p no:cacheprovider` → `python
  runtime/tools/sync_readme.py --check`.

## Run record

- Actions run URL: https://github.com/wahyunuriman999/Muse-Skill-Hub/actions/runs/36957095392
- Run ID: 36957095392
- Trigger: push of `7c7a147` to `final-certification` ("GATE 20: fix real CI
  findings — py3.10 tomllib, Windows EDEADLK backoff")
- Date (UTC): 2026-10-02 ~02:45–02:50
- Conclusion: **success** — all 12 jobs green:
  - windows-latest: py3.10 ✓ py3.11 ✓ py3.12 ✓ py3.13 ✓
  - ubuntu-latest:  py3.10 ✓ py3.11 ✓ py3.12 ✓ py3.13 ✓
  - macos-latest:   py3.10 ✓ py3.11 ✓ py3.12 ✓ py3.13 ✓
- Validator warnings on any leg: 0
- Full-suite failures on any leg: 0 (271 passed per job, e.g.
  windows-latest/py3.12: "271 passed in 92.67s")
- Windows-specific tests observed passing on genuine `windows-latest`
  runners: the real msvcrt file-lock path (`skillhub/filelock.py`),
  20-process spawn race tests for approval consumption, idempotency
  reservation and file-lock exclusivity, plus the new EDEADLK-backoff
  regression tests.

## What the earlier runs found (and fixed)

- Run 36955547751 (first): 12/12 failed the suite — `test_wheel_build_reproducible`
  needed the `build` package (absent from CI), and
  `test_filelock_module_has_platform_branches` hardcoded `platform_name()
  == "unix"`. Both fixed in `de57191`.
- Run 36956035719 (second): 9/12 green — py3.10 legs failed because
  `tools/dependency_audit.py` used stdlib `tomllib` (3.11+ only); fixed
  with a `tomli` fallback. windows-latest/py3.10 additionally hit a rare
  CRT `EDEADLK` under 20-process lock contention; fixed with a bounded
  backoff in `_acquire` plus regression tests. Fixed in `7c7a147`.
- Run 36957095392 (third): 12/12 green. The CI did its job — it caught
  three genuine defects no Linux-only run could see.

## GATE 2 repair statement

GATE 2 (commit `efadd5f`) held the Windows-compatibility implementation
(`skillhub/filelock.py`: msvcrt on Windows, fcntl on Unix, no top-level
`import fcntl`) with Linux-emulated evidence only. This CI run is the first
execution of the suite on genuine `windows-latest` runners. All four
Windows legs are green, so the GATE 2 ledger entry flips to COMPLETE and
the 2026-10-01 premature "GATE 2 COMPLETE" wording stands corrected by
this document — history is not rewritten.

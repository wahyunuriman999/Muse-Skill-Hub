# Release Reproducibility — GATE 21

Executed 2026-10-02 (UTC) against `origin/final-certification` at
`bc2d2c40822b922bdefc363d3a680761d2f13e62`.

## 1. Clean checkout

Fresh `git clone --branch final-certification` of
`https://github.com/wahyunuriman999/Muse-Skill-Hub` into a new directory
(`~/workspace/cert-checkouts/g21-clean` — not `/tmp`, which is disposable).
HEAD verified: `bc2d2c4`, matching `origin/final-certification`. No build
artifacts, no venv, no prior state.

## 2. Reproducible wheel

Two independent `python -m build --wheel` runs from the clean checkout,
seconds apart, produced:

- `muse_skill_hub_runtime-2.2.0-py3-none-any.whl` (both runs)
  (GATE 21 ran before the version bump; the current release artifact is
  `muse_skill_hub_runtime-2.2.1-py3-none-any.whl`, rebuilt and re-verified
  in the post-freeze micro-fix — see `POST_FREEZE_MICROFIX.md`.)

Comparison of the two wheels: identical namelist, and SHA-256 of every
file inside identical — **zero differing files**. The release artifact is
byte-reproducible from the same source tree.

## 3. Fresh installation outside the checkout

- New virtualenv (`~/workspace/cert-checkouts/g21-venv`), created from
  system Python — no access to the certification venv or the source tree.
- Installed only the wheel + `pytest`/`pytest-asyncio` (test runner).
- `python -m skillhub.cli validate` against the installed package:
  **RESULT: PASS (0 warnings)**.
- Full test suite (`tests/`, run from the clean checkout against the
  *installed* `skillhub` package): **265/265 passed** —
  247 in the main run plus 18 in `test_v22_hardening.py` (including the
  20-process spawn race tests and the README drift check).
- Gate tests in `runtime/tests/test_v221_reproducibility.py` additionally
  assert, in-repo: pyproject version == `skillhub.__version__`, the wheel
  ships every skill module (no partial tree), and two wheel builds from the
  tree are content-identical.

## Conclusion

The v2.2.1 release can be built reproducibly from a clean checkout and
installed fresh with the validator and the entire suite green against the
installed artifact. GATE 21 COMPLETE.

# PyPI Readiness Checklist — `muse-skill-hub-runtime`

**Date:** 2026-10-02
**Scope:** Read-only audit of `runtime/pyproject.toml` and build artifacts. No repo changes, no commits, nothing uploaded.
**Working tree:** `~/workspace/muse-skill-hub`, branch `v2.3.0-dev` (HEAD `fcd6c57`)
**Method:** `python -m build` (sdist + wheel) → `twine check` → wheel/sdist content inspection → `pip install` smoke test → PyPI JSON API name check.

## Verdict: NOT READY — 3 blockers, all cheap to fix

The package builds cleanly and `twine check` passes, but three issues must be fixed before a safe first upload. None of them require re-certification of the runtime itself; they are packaging-metadata fixes.

---

## BLOCKERS (fix before upload)

### B1 — Deprecated `project.license` table form (`runtime/pyproject.toml:8`)

```toml
license = { text = "AGPL-3.0-only" }
```

`python -m build` emits:

> `WARNING 'project.license' as a TOML table is deprecated. Please use a simple string containing a SPDX expression for 'project.license'. ... By 2027-Feb-18, you need to update your project and remove deprecated calls or your builds will no longer be supported.`

Consequences of the current form:
- Builds will **break outright** once setuptools removes the deprecated path (deadline 2027-02-18).
- PyPI renders it as plain `License: AGPL-3.0-only` text with **no SPDX validation and no license link**.

**Fix (one line, `runtime/pyproject.toml:8`):**

```toml
license = "AGPL-3.0-only"
```

`AGPL-3.0-only` is a valid SPDX identifier; with the string form, setuptools emits `License-Expression: AGPL-3.0-only` (Metadata-Version 2.4, already in use), which PyPI validates and renders with a proper license link.

### B2 — AGPL license text file is not shipped in the artifacts

The only license file lives at the repo root (`LICENSE`), which is **outside** the packaging root (`runtime/`). Verified in the built artifacts:

- Wheel (`muse_skill_hub_runtime-2.2.1-py3-none-any.whl`, 407 files): **zero** license files.
- Sdist (`muse_skill_hub_runtime-2.2.1.tar.gz`, 542 files): **zero** license files.

AGPL-3.0 requires conveying the license text to recipients; the distributed package currently does not contain it, and PyPI shows no downloadable license file.

**Fix (pick one):**
1. Copy the root `LICENSE` into `runtime/LICENSE` (keep the root copy as the repo's canonical one). setuptools ≥ 77 auto-includes `LICENSE*` from the project root into both sdist and wheel (PEP 639) — no config change needed.
2. Or declare it explicitly: `license-files = ["../LICENSE"]` — less robust, parent-dir globs are fragile; option 1 is preferred.

### B3 — Version/tree mismatch: `2.2.1` on the `v2.3.0-dev` branch (`runtime/pyproject.toml:3`)

The branch is `v2.3.0-dev`, but `version` is still `2.2.1` — and `runtime/` on this branch **differs** from the certified v2.2.1 tag (the attribution commit changed `runtime/pyproject.toml` authors and `runtime/README.md` after the freeze). Uploading now would mint a **second, different "2.2.1" artifact** on PyPI, contradicting the project's own tag/release source-of-truth discipline.

**Fix (pick one before upload):**
- Publish `2.2.1` built from the **`v2.2.1` tag** (byte-identical to the certified GitHub release wheel), or
- Publish `2.3.0` from the certified v2.3.0 release (version bumped to `2.3.0`, certification PASS 2026-10-04).

Do not publish version `2.2.1` built from `v2.3.0-dev`.

---

## READY (verified, no action needed)

| # | Item | Evidence |
|---|------|----------|
| R1 | **Name available** | `https://pypi.org/pypi/muse-skill-hub-runtime/json` → **404** (name free). (`muse-skill-hub` is also 404, but the package is named `muse-skill-hub-runtime` per `runtime/pyproject.toml:2`.) |
| R2 | **sdist + wheel build cleanly** | `python -m build` succeeded: `muse_skill_hub_runtime-2.2.1.tar.gz` (216 KB) + `muse_skill_hub_runtime-2.2.1-py3-none-any.whl` (500 KB). |
| R3 | **`twine check` passes** | `PASSED` on both sdist and wheel — long description (`runtime/README.md` via `runtime/pyproject.toml:6`) renders valid Markdown. |
| R4 | **All 97 skills packaged** | Wheel contains 97 `catalog/*/SKILL.md` + 97 `catalog/*/manifest.yaml` (`[tool.setuptools.package-data]`, `runtime/pyproject.toml:24-26`). Sdist likewise complete (542 files). |
| R5 | **Entry points valid** | `skillhub = skillhub.cli:main` (`skillhub/cli.py:234`) and `skillhub-server = skillhub.server:main` (`skillhub/server.py:80`) both exist; post-install `skillhub` CLI runs. |
| R6 | **Dependencies resolvable** | Fresh `pip install` of the wheel succeeded; `mcp>=1.0,<2` resolved to a 1.x release (2.2.0 is latest on PyPI, correctly excluded by the `<2` cap); `httpx`, `pyyaml`, `cryptography`, `jsonschema` all on PyPI. |
| R7 | **Core metadata present** | `description` (`:4`), `authors = [{ name = "Wahyu Nur Iman" }]` (`:5`), `requires-python = ">=3.10"` (`:7`) all valid. |
| R8 | **No malware/secret risk in artifacts** | Sdist contains no `build/` dir output; only benign `*.egg-info` regeneration metadata (see hygiene note H1). |

## SHOULD-FIX (recommended, not blocking)

- **S1 — No classifiers** (`runtime/pyproject.toml` has no `classifiers` key). Upload works without them, but the PyPI page will lack OS/Python/license badges. Recommended additions:
  ```toml
  classifiers = [
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Programming Language :: Python :: 3.13",
      "License :: OSI Approved :: GNU Affero General Public License v3",
      "Operating System :: OS Independent",
      "Intended Audience :: Developers",
      "Topic :: Scientific/Engineering :: Artificial Intelligence",
  ]
  ```
- **S2 — No `[project.urls]`** — the PyPI sidebar will show no Homepage/Repository links (`pip show` reports empty `Home-page`). Recommended:
  ```toml
  [project.urls]
  Homepage = "https://github.com/wahyunuriman999/Muse-Skill-Hub"
  Repository = "https://github.com/wahyunuriman999/Muse-Skill-Hub"
  Documentation = "https://github.com/wahyunuriman999/Muse-Skill-Hub#readme"
  Changelog = "https://github.com/wahyunuriman999/Muse-Skill-Hub/releases"
  ```
- **H1 — Build hygiene:** `runtime/` contains stale `build/` and `muse_skill_hub_runtime.egg-info/` dirs; the egg-info leaked into the sdist (harmless). Delete both before the release build for a pristine sdist.

## OWNER-ACTION (only Wahyu can do these)

1. **Create a PyPI account** at https://pypi.org/account/register/ and **enable 2FA** (required).
2. **Verify the account email** (upload is blocked until verified).
3. **Create an API token** at https://pypi.org/manage/account/token/ — scope it to the project `muse-skill-hub-runtime` (for the very first upload, an account-scoped token is simplest; the project name is claimed by the first successful upload).
4. **Upload** (from `runtime/`, after B1–B3 are fixed and a clean rebuild):
   ```bash
   python -m build
   twine upload dist/*
   ```
   Use the token as password with username `__token__`. **Do not paste the token into chat** — pass it via `TWINE_PASSWORD` env var or `~/.pypirc` (mode 600).
5. Optional but recommended: set up **Trusted Publishing** (GitHub Actions → PyPI) afterwards so future releases upload without long-lived tokens.

## AGPL-3.0 on PyPI — rendering note

- PyPI **accepts** AGPL-3.0 packages; there is no policy block.
- With the current `{ text = ... }` form, the project page shows `License: AGPL-3.0-only` as **unlinked plain text** and it does not appear in PyPI's license-filtered search facets the way SPDX expressions do.
- After the B1 fix (`license = "AGPL-3.0-only"`), PyPI validates the SPDX expression and renders it as a **linked license** (to the SPDX/AGPL text). This is the correct, supported path.

## Appendix — commands run

```bash
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/muse-skill-hub-runtime/json  # 404
curl -s https://pypi.org/pypi/mcp/json | python3 -c ...                                    # mcp latest 2.2.0
cd runtime && python -m build --outdir /tmp/pypi-audit-dist                                # OK (1 warning: B1)
twine check /tmp/pypi-audit-dist/*                                                         # PASSED x2
pip install /tmp/pypi-audit-dist/*.whl && skillhub --help                                  # OK
```

Build artifacts were written to `/tmp/pypi-audit-dist/` (ephemeral); the repo tree was left untouched — `git status` shows only this new file as untracked.

---

## Addendum — 2026-10-04: all blockers resolved, package READY for upload

Re-audit of the `v2.3.0` release tree (`main`, tag `v2.3.0` → `4666b13`):

| Blocker | Status | Evidence |
|---|---|---|
| B1 — deprecated `project.license` table | **RESOLVED** | `runtime/pyproject.toml:8` is now `license = "AGPL-3.0-only"` (string form) |
| B2 — license file not shipped | **RESOLVED** | `runtime/LICENSE` exists; verified present inside the built wheel |
| B3 — version/tree mismatch | **RESOLVED** | `version = "2.3.0"`, built from the certified release tag |

Release artifact verification (built from the certified tag):

- `Metadata-Version: 2.4`, `Name: muse-skill-hub-runtime`, `Version: 2.3.0`
- `Author: Wahyu Nur Iman`
- `License-Expression: AGPL-3.0-only` — PyPI will validate and render this as a linked SPDX license
- `twine check`: PASSED (wheel + sdist)
- PyPI name `muse-skill-hub-runtime`: **available** (404 on the JSON API, checked 2026-10-04)

**Verdict: READY.** The only remaining step is the upload itself, which needs the maintainer's PyPI account and API token (secure flow, never in chat). Nothing else in the repo blocks it.

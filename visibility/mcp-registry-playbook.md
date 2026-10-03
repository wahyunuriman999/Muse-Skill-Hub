# MCP Registry Submission Playbook — muse-skill-hub

**Target:** the official MCP Registry at <https://registry.modelcontextprotocol.io>
(run by the MCP project; community PRs to `modelcontextprotocol/servers` are no longer accepted —
this registry is the canonical submission path).

**Our identity:** `io.github.wahyunuriman999/muse-skill-hub`
**PyPI distribution:** `muse-skill-hub-runtime` (not yet published — see Step 2)
**Research date:** 2026-10-02. The registry is officially in **preview**
(per its Terms of Service, effective 2025-09-02): breaking changes or data
resets are possible before GA. Re-check the schema URL before publishing.

---

## 1. How the registry works (mental model)

- The registry stores **metadata only** (`server.json`), not code. Your package
  still lives on PyPI; the registry points at it.
- Publishing is **self-service via CLI** — no human review queue, no approval
  wait. A successful `mcp-publisher publish` goes live immediately.
- **Cost: free.** No fees found anywhere in the official docs or ToS.
- Anti-squatting is enforced **cryptographically at publish time** in two ways:
  1. **Namespace ownership:** `mcp-publisher login github` (GitHub OAuth device
     flow) proves you control `github.com/wahyunuriman999`, which authorizes
     publishing under `io.github.wahyunuriman999/*`.
  2. **Package ownership:** the registry fetches the *live PyPI page* for your
     package and requires it to contain an `mcp-name:` marker matching your
     server name (details in Step 1).
- The published metadata you submit (name, description, URLs, identifiers) is
  dedicated to the **public domain under CC0 1.0** per the registry ToS. This
  covers registry metadata only — **not** your package, which keeps its own
  license.

### License: is AGPL-3.0 accepted?

**Yes, for the official registry.** The official Terms of Service
(<https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/registry/terms-of-service.mdx>)
contain **no license allowlist**. Its prohibitions cover malware, defamation,
spam/impersonation, and similar abuse — nothing about copyleft. The registry
explicitly "supports both open-source and closed-source servers."

⚠️ One caveat: **downstream aggregators have their own rules.** StackLok's
ToolHive catalog, for example, excludes copyleft licenses (AGPL-3.0, GPL-*)
from *its* catalog. That does not block the official registry listing, but an
AGPL-3.0 package may be skipped by some third-party directories that mirror
the registry.

---

## 2. Prerequisites checklist

| # | Item | Status | Owner |
|---|------|--------|-------|
| 1 | `server.json` drafted & schema-valid | ☐ prepare (Muse) | Muse |
| 2 | `<!-- mcp-name: … -->` marker in `runtime/README.md` | ☐ repo change | Muse (commit) / Wahyu (merge) |
| 3 | Console-script alias `muse-skill-hub-runtime` → `skillhub.server:main` | ☐ repo change | Muse (commit) / Wahyu (merge) |
| 4 | Cut a release (e.g. `v2.3.0`) containing 2+3 | ☐ release | Wahyu |
| 5 | Publish that release to **PyPI** (`muse-skill-hub-runtime`) | ☐ **not done — needs Wahyu's PyPI account** | Wahyu |
| 6 | `mcp-publisher` CLI installed | ☐ 2 min | Muse or Wahyu |
| 7 | `mcp-publisher login github` (interactive OAuth as @wahyunuriman999) | ☐ **needs Wahyu** | Wahyu |
| 8 | `mcp-publisher publish` | ☐ after 1–7 | Wahyu (or CI, see §7) |

**Why items 2–3 matter:**

- **Marker (item 2).** PyPI metadata is **immutable per release**. The registry
  verifies ownership by reading the *published* PyPI description and looking
  for the exact string `<!-- mcp-name: io.github.wahyunuriman999/muse-skill-hub -->`.
  A release published before the marker existed can never satisfy the check —
  the marker must ship in a **new** PyPI release. Since we have never published
  to PyPI at all, we just need the marker present *before the first upload*.
- **Console-script alias (item 3).** With `runtimeHint: "uvx"`, clients launch
  the server as `uvx <identifier>` — i.e. `uvx muse-skill-hub-runtime`. `uvx`
  resolves the executable from the package's console scripts, and today our
  scripts are named `skillhub-server` / `skillhub`, **not**
  `muse-skill-hub-runtime`. Recent successful publishers (e.g. `mtdata-mcp`,
  `uniprot-mcp`, both 2026) solved exactly this by adding a script alias whose
  name equals the PyPI distribution name. Without it, `uvx muse-skill-hub-runtime`
  will not resolve to our server entrypoint.

---

## 3. Step-by-step

### Step 1 — Repo prep (Muse prepares, Wahyu merges; part of next release)

**1a. Add the ownership marker** to the top of `runtime/README.md`
(that file is the PyPI long description: `pyproject.toml` sets `readme = "README.md"`):

```html
<!-- mcp-name: io.github.wahyunuriman999/muse-skill-hub -->
```

Keep it as an HTML comment so it stays invisible on the rendered PyPI/GitHub page.

**1b. Add the console-script alias** in `runtime/pyproject.toml`:

```toml
[project.scripts]
skillhub-server = "skillhub.server:main"
skillhub = "skillhub.cli:main"
muse-skill-hub-runtime = "skillhub.server:main"   # <-- ADD: makes `uvx muse-skill-hub-runtime` resolve
```

**1c. Sanity-check the launch locally** (verifies the alias works via uvx):

```bash
cd runtime
pip install -e .
uvx --from muse-skill-hub-runtime muse-skill-hub-runtime --help   # or: python -m build && uvx --from ./dist/*.whl muse-skill-hub-runtime
```

The server boots over stdio and needs **no** environment variables to start
(credentials are per-skill and optional; the server reports them honestly as
missing), so `environmentVariables` can stay empty in `server.json`.

### Step 2 — Publish the release to PyPI (🔑 Wahyu only)

Requires Wahyu's own PyPI account (`__token__` API token). Muse cannot do this.

```bash
cd runtime
rm -rf dist build *.egg-info
python -m build
twine check dist/*
twine upload dist/*
```

Then **confirm the marker is live on PyPI** (the registry reads this, not your working tree):

```bash
VERSION="2.3.0"   # the exact version just uploaded
curl -fsS "https://pypi.org/pypi/muse-skill-hub-runtime/${VERSION}/json" \
  | jq -e --arg marker "<!-- mcp-name: io.github.wahyunuriman999/muse-skill-hub -->" \
      '(.info.description // "") | contains($marker)' \
  && echo "MARKER LIVE" || echo "MARKER MISSING — do not proceed to Step 6"
```

PyPI can take a few minutes to index; wait until the check prints `MARKER LIVE`.

### Step 3 — Write `server.json` (Muse prepares; commit at repo root)

Full example below (§4). Validate it against the live schema **before** the login dance:

```bash
# Option A: publisher CLI (needs mcp-publisher v1.3+)
mcp-publisher validate server.json        # expect: ✅ server.json is valid

# Option B: ajv (no publisher install needed)
npm install -g ajv-cli
ajv validate \
  -s https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json \
  -d server.json --spec=draft2020
```

Gotchas the schema enforces (verified against the live schema file):
- `description` ≤ **100 characters** (hard `maxLength`; longer → publish rejected).
- Top-level `version` **and** `packages[0].version` must both be set and **match
  the PyPI release exactly**. No ranges, no `"latest"`.
- `name` must match `^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$` (one `/`), ≤ 200 chars.

### Step 4 — Install `mcp-publisher` (anyone)

```bash
# Homebrew (macOS/Linux)
brew install mcp-publisher

# …or direct binary (Linux example; adjust for platform)
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" \
  | tar xz mcp-publisher
sudo mv mcp-publisher /usr/local/bin/

mcp-publisher --help   # expect: init, login, logout, publish, validate, status
```

Releases: <https://github.com/modelcontextprotocol/registry/releases>

### Step 5 — Authenticate (🔑 Wahyu only — interactive)

```bash
mcp-publisher login github
```

This opens a GitHub **device-flow** prompt: visit the URL, enter the code,
authorize as **@wahyunuriman999**. It proves ownership of the
`io.github.wahyunuriman999/*` namespace and stores a JWT in
`~/.config/mcp-publisher/token.json`.

Notes:
- The JWT **expires quickly** — run `login` immediately before `publish` in the
  same session (multiple publishers report 422/auth failures otherwise).
- If it fails: `mcp-publisher logout` then `login github` again.
- CI alternative: `mcp-publisher login github-oidc` inside GitHub Actions (see §7).

### Step 6 — Publish (🔑 Wahyu, right after login)

From the directory containing `server.json`:

```bash
mcp-publisher publish
# or explicitly: mcp-publisher publish server.json
```

The CLI validates `server.json`, checks namespace ownership, fetches the live
PyPI description for the `mcp-name` marker, and uploads. **On success the entry
is live immediately** — there is no review queue.

### Step 7 — Verify (anyone)

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=muse-skill-hub" \
  | jq '.servers[] | {name, version, description}'

# Canonical record URL:
# https://registry.modelcontextprotocol.io/v0/servers/io.github.wahyunuriman999/muse-skill-hub
```

---

## 4. Reference `server.json` for muse-skill-hub

Field-by-field this follows the schema at
`https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`
(required: `name`, `description`, `version`; per-package required:
`registryType`, `identifier`, `transport`). **Replace `2.3.0` with the exact
version you publish to PyPI** — all three version fields must agree.

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.wahyunuriman999/muse-skill-hub",
  "title": "Muse Skill Hub",
  "description": "LLM-agnostic capability runtime: 97 skills as typed, permission-enforced MCP tools (open source)",
  "version": "2.3.0",
  "websiteUrl": "https://github.com/wahyunuriman999/Muse-Skill-Hub",
  "repository": {
    "url": "https://github.com/wahyunuriman999/Muse-Skill-Hub",
    "source": "github",
    "id": "1400209464",
    "subfolder": "runtime"
  },
  "icons": [
    {
      "src": "https://raw.githubusercontent.com/wahyunuriman999/Muse-Skill-Hub/main/visibility/social-preview-small.jpg",
      "mimeType": "image/jpeg"
    }
  ],
  "packages": [
    {
      "registryType": "pypi",
      "registryBaseUrl": "https://pypi.org",
      "identifier": "muse-skill-hub-runtime",
      "version": "2.3.0",
      "runtimeHint": "uvx",
      "transport": { "type": "stdio" }
    }
  ],
  "_meta": {
    "io.modelcontextprotocol.registry/publisher-provided": {
      "io.github.wahyunuriman999": {
        "muse-skill-hub-runtime": {
          "tags": ["ai-agents", "mcp", "automation", "tools", "open-source"]
        }
      }
    }
  }
}
```

Notes on the choices above:
- `description` is **96 chars** — under the 100-char hard limit.
- `repository.id` (`1400209464`, verified via `gh api`) is optional but
  recommended: it lets the registry detect repository deletion/re-creation
  (resurrection attacks).
- `repository.subfolder: "runtime"` — the package lives in `runtime/`, not the repo root.
- `runtimeHint: "uvx"` + stdio is the standard 2026 pattern for PyPI servers;
  clients compose `uvx muse-skill-hub-runtime`. This is why the console-script
  alias in Step 1b is required.
- `icons` is optional; the `src` above assumes a small JPG is committed at that
  path — adjust or drop the block if you prefer. Must be HTTPS.
- `_meta.io.modelcontextprotocol.registry/publisher-provided` is the
  schema-sanctioned extension point for downstream registries (tags, tiers).
  Optional; harmless to keep minimal.
- No `environmentVariables`: the server boots with none (per-skill credentials
  are optional and reported honestly at runtime).

---

## 5. Versioning & updates

- **New version:** bump `runtime/pyproject.toml` → publish to PyPI → bump both
  `version` fields in `server.json` to match → commit → `mcp-publisher publish`
  again. Same flow every time; the GitHub login token is cached between runs
  (re-login when it expires).
- **Never** point `packages[].version` at a PyPI release that lacks the
  `mcp-name` marker — publish will be refused.
- **Deprecate an old version** (reported by third-party publishers; verify flags
  with `mcp-publisher status --help`):
  ```bash
  mcp-publisher status --status deprecated --message "Upgrade to 2.3.0" \
    io.github.wahyunuriman999/muse-skill-hub 2.2.1
  ```

## 6. Namespacing & identity (how `io.github.wahyunuriman999` is claimed)

- Namespace `io.github.<gh-username>/*` is claimed **purely via GitHub OAuth**
  (`mcp-publisher login github` as @wahyunuriman999). No DNS, no manual
  approval, no pre-registration.
- The repo's canonical GitHub owner and the server namespace must stay aligned
  (don't publish `io.github.wahyunuriman999/…` from a fork owned by someone else).
- Custom-domain namespaces (e.g. `com.example/…`) need DNS TXT verification —
  **not applicable** to us.
- For local dry-runs against a throwaway registry, `mcp-publisher login none
  --registry=<url>` exists, but anonymous publishing requires names under
  `io.modelcontextprotocol.anonymous/` — not our path.

## 7. Optional: automate via GitHub Actions (OIDC, no stored tokens)

Reported pattern (verify against the registry repo's docs when implementing):

```yaml
# .github/workflows/publish-registry.yml
name: Publish to MCP Registry
on:
  push:
    tags: ["v*"]
permissions:
  id-token: write
  contents: read
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install mcp-publisher
        run: |
          curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_linux_amd64.tar.gz" \
            | tar xz mcp-publisher
      - name: Publish
        run: |
          ./mcp-publisher login github-oidc
          ./mcp-publisher publish
```

⚠️ UNVERIFIED detail: the exact OIDC trust configuration the registry expects
(e.g. required `id-token` permissions, audience). The `login github-oidc`
subcommand itself is confirmed by multiple publishers; wire it up by following
the registry repo's current CI docs and test on a pre-release tag first.

---

## 8. Terms & policy summary (from the official ToS)

- Must be 18+; comply with applicable law.
- Prohibited: malware, harassment/defamation, disrupting the registry,
  spam/impersonation (incl. implying false affiliation), unlawful gambling,
  life-safety use cases, ITAR data.
- Submitted **metadata** is CC0-1.0 public domain (metadata only — your code
  keeps its AGPL-3.0 license).
- Publishing metadata is public: your GitHub username and description will be
  visible; downstream registries may enrich/scan it.
- Branding rule: you may say "listed in the Official MCP Registry", not imply
  partnership or endorsement.

## 9. Who does what (ownership matrix)

| Step | Doable by Muse now | Needs Wahyu |
|------|--------------------|-------------|
| Draft `server.json`, validate against schema | ✅ | — |
| Add `mcp-name` marker + script alias (commit) | ✅ (commit; merge = Wahyu) | merge/release |
| Create PyPI account / API token | — | 🔑 Wahyu |
| `twine upload` first release | — | 🔑 Wahyu |
| `mcp-publisher login github` (browser OAuth) | — | 🔑 Wahyu (interactive) |
| `mcp-publisher publish` | — | 🔑 Wahyu (or pre-authorized CI) |
| Verify listing via public API | ✅ | — |

**Critical path:** items 2–5 of the checklist are all release-gated. The
efficient order is: (a) Muse preps the two repo changes + `server.json` now;
(b) they ride along in the next release (v2.3.0); (c) Wahyu publishes to PyPI;
(d) Wahyu runs login + publish (∼5 minutes, one sitting — login and publish
back-to-back because the JWT expires quickly).

## 10. Sources

- Official registry repo & publisher CLI: <https://github.com/modelcontextprotocol/registry>
- Server schema (draft, auto-generated): <https://raw.githubusercontent.com/modelcontextprotocol/registry/main/docs/reference/server-json/draft/server.schema.json>
- Pinned schema used below: <https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json>
- Official ToS: <https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/registry/terms-of-service.mdx>
- Registry "about" (namespace mgmt, package registries): <https://github.com/modelcontextprotocol/modelcontextprotocol/blob/HEAD/docs/registry/about.mdx>
- Publisher flow walkthroughs (third-party, cross-checked): solar-punk-ltd/swarm-mcp,
  cesteral/mcp-open-advertising, ymxlx/polis-protocol, zowe/zowe-mcp,
  orholam/kanban_ai, dataviking-tech/althing, smaniches/uniprot-mcp,
  emerzon/mtdata-mcp, azzy-h/mcp-video-frames

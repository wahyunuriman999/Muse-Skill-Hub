# Roadmap — Muse-Skill-Hub

Where this project is headed. Dates are intentionally absent: this is a
direction, not a promise. Items move when they are genuinely ready, not
when a calendar says so.

## Shipped — v2.3.0 (2026-10-04)

- 97 skills · 96 executable drivers · 222 MCP tools · 313 tests, all passing
- Full independent-style certification: 27/27 gates, 0 blockers
- Validator clean: 0 warnings across all skills
- Community setup: discussions, code of conduct, contributing guide,
  security policy, issue/PR templates
- Per-skill Depth markers (Full / Standard / Limited / Stub)
- Commercial licensing path alongside AGPL-3.0-only
- Live end-to-end proof: Gmail → Google Sheets via the connected services

## Next — distribution

1. **PyPI** — package `muse-skill-hub-runtime` is built, `twine check`
   passes, and the name is reserved in spirit (verified available).
   Upload happens when the maintainer's account and token are in place.
   See `visibility/pypi-readiness.md`.
2. **MCP Registry** — identity `io.github.wahyunuriman999/muse-skill-hub`
   (metadata in `visibility/server.json`). Publication follows a successful
   PyPI release, since the registry verifies the `mcp-name` marker on the
   live PyPI page. Playbook: `visibility/mcp-registry-playbook.md`.

## Next — live contract coverage

Most third-party drivers are verified only as *contracts* (typed, mocked,
honest about what they need). The goal is to keep expanding the set of
drivers exercised against real APIs and recording the results in
`visibility/live-contracts-report.md`. Gmail and Google Sheets drivers are
first in line.

## Next — community skills

The `Community skills` section in the README accepts PRs from other
authors in the same open `SKILL.md` format. One merged so far; more are
welcome. External skills stay external — linked, not vendored.

## Deliberately out of scope

- Multi-user SaaS hosting and tenant isolation
- Distributed exactly-once delivery guarantees
- Silent retries of uncertain post-call crashes

These are honest product boundaries, not missing features. See the README
for the full statement.

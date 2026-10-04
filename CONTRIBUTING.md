# Contributing to Muse Skill Hub

Thanks for your interest in contributing. This project holds itself to a
high bar — every skill is executable, tested, and honestly described — and
contributions are held to the same bar.

## Ways to contribute

- **New skills**: add a skill following the `SKILL.md` format below.
- **Driver improvements**: turn a structural driver into a live-tested one,
  fix a bug, or narrow an honest limitation.
- **Docs**: fix errors, clarify explanations, add examples.
- **Community skills**: built a skill for another LLM in the same open
  `SKILL.md` format? Add it to the **Community skills** table in
  `README.md` (one row: name, link, one-line description, license).

## Skill format

Every skill lives in `skills/<skill-name>/` with a `SKILL.md` frontmatter:

```yaml
---
name: my-skill
title: Human-readable title
description: One or two sentences, no placeholders.
license: AGPL-3.0-only
---
```

Rules:

- **English** for all code, docs, comments, and commit messages.
- **No placeholders.** If a capability can't be built honestly, say so in
  the description (see the honest-stub convention in existing skills).
- **No secrets.** Never commit API keys, tokens, or credentials.
- **Tests.** New executable behavior needs tests under `runtime/tests/`.
  Run the suite before opening a PR (see below).

## Development workflow

```bash
cd runtime
../.venv/bin/python -m pytest tests/ -q          # full suite
../.venv/bin/python tools/sync_readme.py --check # generated docs in sync
```

The conformance validator must pass with zero warnings:

```bash
../.venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from skillhub.cli import validate
assert validate() == 0"
```

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make focused commits with clear English messages.
3. Open a PR against `main` describing **what** changed and **how you
   verified it** (tests run, validator output, live evidence where it
   applies).
4. CI must be green. The maintainer may ask for changes — that's normal.

## Ground rules

- Be kind and precise. Review the code, not the person.
- Don't claim more than you prove: every guarantee needs a test or
  live evidence behind it.
- Don't re-license anyone's work. Community skill rows link out; their
  licenses stay theirs.

## Questions?

Open a [Discussion](https://github.com/wahyunuriman999/Muse-Skill-Hub/discussions)
— that's what it's for.

---

*Copyright © 2026 Wahyu Nur Iman.*

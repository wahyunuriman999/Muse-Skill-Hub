# Skill Manifest spec (v1)

`skills/<name>/manifest.yaml` is the machine-readable canonical contract for
a skill. `SKILL.md` (human instructions), `driver.py` (execution), the MCP
schema, tests and docs are all validated against it by
`python -m skillhub.cli validate`.

```yaml
schema_version: "1"
name: github
version: 1.0.0
title: GitHub
description: Search repos, manage issues and PRs via the GitHub REST API.
kind: skill                 # skill | router | reference
lifecycle: stable            # draft | experimental | beta | stable | deprecated
actions:
  - name: search_repositories
    type: read               # read | write
    risk: read               # read|write|sensitive|destructive|communication|financial|account|device
    approval: not_required   # not_required | required
    supports_idempotency_key: true
    required_scopes: []      # OAuth/token scopes the action needs; enforced when known
    input_schema:
      type: object
      properties:
        query: {type: string}
      required: [query]
    output_schema:
      type: object
auth:
  required_env: [GITHUB_TOKEN]
  notes: Optional; public read endpoints work without a token.
dependencies: []             # other skill names this skill delegates to
```

## Conformance rules

`skillhub validate` fails a skill on:

- invalid / missing `name`, `title`, `description`, `version`
- duplicate skill names
- action `parameters` using unknown JSON types
- `required` listing a parameter not declared in `parameters`
- unknown `risk` level
- manifest actions ≠ driver actions (drift)
- driver actions not mentioned in `SKILL.md` (doc drift, warning)
- hardcoded secret-looking strings in the driver (warning)

Counts in `README.md` must match `skillhub metadata`.

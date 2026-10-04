# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 2.3.x   | :white_check_mark: |
| < 2.3   | :x:                |

Only the latest release line receives security fixes. Please upgrade
before reporting.

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

Email **wahyunuriman999@gmail.com** with the subject
"SECURITY — Muse Skill Hub" and include:

- What the vulnerability is and where it lives (file, action, endpoint)
- Steps to reproduce, or a minimal proof of concept
- What you think the impact is (who is affected, how)

You will get an acknowledgment within 72 hours. If the report is confirmed,
a fix will be prepared and released, and you will be credited in the
release notes (unless you prefer to stay anonymous).

## Scope notes

- This project is a **trusted local single-user runtime**. It is not
  multi-user SaaS: there is no tenant isolation and no remote
  authentication to attack in the default setup.
- The threat model lives in `runtime/THREAT_MODEL.md` (and the
  certification reports under `certification/`). Reports that contradict
  the documented model get priority attention.
- Third-party provider credentials are yours: never send real API keys
  or tokens in a report — use placeholders and describe where the real
  value would go.

---

*Copyright © 2026 Wahyu Nur Iman.*

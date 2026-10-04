# Live end-to-end example: Gmail → Google Sheets

**Date:** 2026-10-04
**Status:** executed live against real Google APIs (read + write), verified by read-back.

## What was proven

A real Gmail inbox read followed by a real Google Sheets write, end to end:
triage the latest inbox message → create a spreadsheet → append one row of
the message's metadata → read the row back.

## The flow

1. **Read** — listed the latest inbox message (sender, subject, date only;
   no body content was used).
2. **Create** — created a new spreadsheet titled `Skill Hub e2e demo`.
3. **Write** — appended one header row plus one data row
   (`Sender | Subject | Date`).
4. **Verify** — read `Sheet1!A1:C2` back; the written values matched.

## Honest boundary

This example was executed through the assistant's connected Google Workspace
account, **not** through this repo's `gmail.py` / `google_sheets.py` drivers.
Those drivers authenticate with a raw `GOOGLE_OAUTH_TOKEN` environment
variable, which was not available in this run — their live-contract specs
therefore remain `SKIP` in `live-contracts-report.md`.

So: the **API flow** (Gmail read → Sheets write) is proven live. The
**driver code paths** are not yet live-tested. No claim beyond that is made.

## Reproduce it

```bash
# 1. latest inbox message metadata
hatch_gws_cli gmail +triage --query 'in:inbox' --max 1 --format json

# 2. create the spreadsheet (returns spreadsheetId)
hatch_gws_cli sheets spreadsheets create \
  --json '{"properties":{"title":"Skill Hub e2e demo"}}'

# 3. append header + one data row
hatch_gws_cli sheets +append --spreadsheet <ID> \
  --json-values '[["Sender","Subject","Date"],["<from>","<subject>","<date>"]]'

# 4. verify
hatch_gws_cli sheets +read --spreadsheet <ID> --range 'Sheet1!A1:C2'
```

`hatch_gws_cli` is the assistant's Google Workspace CLI; it needs a
connected Google account. The repo drivers (`runtime/skillhub/skills/`)
are standalone and take `GOOGLE_OAUTH_TOKEN` instead.

---

*Copyright © 2026 Wahyu Nur Iman.*

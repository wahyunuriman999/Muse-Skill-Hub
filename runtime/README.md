# ⚡ Muse Skill Hub — Executable MCP Runtime

<!-- METRICS:START -->
_Generated from registry + test suite — do not hand-edit. Run `python tools/sync_readme.py`._

**Version 2.2.0** · **97 skills** · **94 executable drivers** (3 honest stubs) · **210 MCP tools** · **224 passing tests**
<!-- METRICS:END -->

This is the **executable layer** of Muse Skill Hub. It turns the skill catalog
( `runtime/skillhub/catalog/*/SKILL.md` ) into **real, callable MCP tools** that any MCP-compatible
LLM client (Claude Desktop, etc.) can use plug-and-play.

## How it works

```
runtime/skillhub/catalog/*/SKILL.md  ──catalog──▶  skillhub/registry.py  ──▶  MCP server (stdio)
                                           │
                        ┌──────────────────┴──────────────────┐
                        │  real drivers (executable)             │
                        │  catalog-only (honest stubs)           │
                        └─────────────────────────────────────┘
```

- **Every action is its own MCP tool** (`github_search_repositories`, …) with
  full JSON input schemas — typed tools, plus `skillhub_search_capabilities`
  for dynamic discovery by natural-language query (exact counts in the metrics
  block above).
- Skills with a driver in `skillhub/skills/` execute **real API calls**.
- Skills without a driver return a structured `driver_not_implemented` response
  (never a fake success) with a pointer to the driver template.
- **Permissions are enforced in code** (`skillhub/policy.py`):
  `read` actions run freely; plain `write` actions need `confirm=true`;
  `sensitive`/`destructive`/`communication`/`financial`/`account`/`device`
  actions need a real approval (`approval_id` bound to the exact
  skill/action/params, single-use, 10-min TTL).
- **Credentials are honest**: missing env vars return `credentials_missing`
  with exact setup instructions — no hallucinated data.
- **Audit log**: every execution is recorded with request_id, risk, approval_id,
  and duration; secrets are redacted. Query with `function-health query_audit_log`.
- **Idempotency**: pass `idempotency_key` on write actions; repeats return the
  first result instead of re-executing.

## Quick start

```bash
cd runtime
pip install -r requirements.txt

# run the MCP server (stdio transport)
python -m skillhub.server
# → "muse-skill-hub v2.2.0: 97 skills registered, 94 with executable drivers, 210 MCP tools."
#   (exact banner line depends on the release; see the metrics block above)
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "muse-skill-hub": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "skillhub.server"],
      "cwd": "/path/to/Muse-Skill-Hub/runtime",
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "SLACK_BOT_TOKEN": "xoxb-..."
      }
    }
  }
}
```

## Implemented drivers

| Skill | Actions | Credentials |
|---|---|---|
| `agent-library` | register_agent, list_agents, get_agent, remove_agent | — |
| `apple-healthkit` | get_daily_metrics, get_sleep, get_workouts | — |
| `asana` | list_tasks, create_task | `ASANA_ACCESS_TOKEN` |
| `booking` | search_flights, search_events, hotel_search_link, restaurant_search_link | — |
| `box` | list_folder, search, get_file_info | `BOX_ACCESS_TOKEN` |
| `calendly` | list_event_types, list_events | `CALENDLY_API_TOKEN` |
| `canva` | list_designs, get_design | `CANVA_ACCESS_TOKEN` |
| `connector-management` | list_connectors, get_connector, set_connector, remove_connector | — |
| `data-control` | explain_collection, export_data, delete_data | — |
| `device-data` | import_snapshot, get_contacts, get_calendar, delete_local_copy | — |
| `dropbox` | list_folder, get_metadata | `DROPBOX_ACCESS_TOKEN` |
| `duffel` | search_offers, create_order | `DUFFEL_ACCESS_TOKEN` |
| `evernote` | list_notebooks, list_notes | `EVERNOTE_DEV_TOKEN` |
| `facebook` | get_profile, get_posts, post_to_feed | `FACEBOOK_ACCESS_TOKEN` |
| `facebook-cli` | run_command | — |
| `figma` | get_file, export_image | `FIGMA_ACCESS_TOKEN` |
| `flightaware` | flight_status | `FLIGHTAWARE_API_KEY` |
| `forget` | remember_fact, list_facts, forget_fact | — |
| `function-health` | runtime_health | — |
| `generate_podcast` | compose_episode | `ELEVENLABS_API_KEY` |
| `ghl` | list_contacts, get_contact, create_contact | `GHL_API_KEY` |
| `github` | search_repositories, get_repository, list_issues, create_issue | — |
| `gmail` | list_messages, get_message, send_message | `GOOGLE_OAUTH_TOKEN` |
| `goals` | create_goal, list_goals, log_progress, complete_goal | — |
| `google-calendar` | list_events, create_event | `GOOGLE_OAUTH_TOKEN` |
| `google-contacts` | list_contacts, create_contact | `GOOGLE_OAUTH_TOKEN` |
| `google-docs` | get_document, create_document | `GOOGLE_OAUTH_TOKEN` |
| `google-drive` | list_files, search_files | `GOOGLE_OAUTH_TOKEN` |
| `google-forms` | create_form, get_responses | `GOOGLE_OAUTH_TOKEN` |
| `google-health-connect` | get_daily_metrics, get_sleep, get_workouts | — |
| `google-sheets` | read_range, append_row | `GOOGLE_OAUTH_TOKEN` |
| `google-slides` | get_presentation, create_presentation | `GOOGLE_OAUTH_TOKEN` |
| `google-tasks` | list_task_lists, list_tasks, create_task, complete_task | `GOOGLE_OAUTH_TOKEN` |
| `healthex` | list_tools, call_tool | `HEALTHEX_AUTH_TOKEN` |
| `idea-management` | add_idea, list_ideas, dismiss_idea | — |
| `image-search` | search_images | `SERPER_API_KEY` |
| `instagram` | get_profile, get_media | `INSTAGRAM_ACCESS_TOKEN` |
| `instagram-messages` | list_conversations, send_message | `INSTAGRAM_PAGE_TOKEN` |
| `klaviyo` | list_lists, list_campaigns | `KLAVIYO_API_KEY` |
| `linear` | list_issues, create_issue | `LINEAR_API_KEY` |
| `media-library` | list_photos, search_photos | — |
| `messaging-channels` | register_channel, list_channels, send_message | — |
| `messenger` | list_conversations, send_message | `MESSENGER_PAGE_TOKEN` |
| `meta-ads` | list_ad_accounts, list_campaigns | `META_ADS_ACCESS_TOKEN` |
| `meta-threads` | get_profile, post_text | `THREADS_ACCESS_TOKEN` |
| `muse-feedback` | submit_feedback, list_feedback | — |
| `muse_db` | list_tables, query, execute_write | — |
| `notion` | search, query_database | `NOTION_TOKEN` |
| `opentable` | search_restaurants, reservation_link | — |
| `outlook-calendar` | list_events, create_event, delete_event | `MICROSOFT_ACCESS_TOKEN` |
| `outlook-contacts` | list_contacts, create_contact | `MICROSOFT_ACCESS_TOKEN` |
| `outlook-mail` | list_messages, send_mail | `MICROSOFT_ACCESS_TOKEN` |
| `paired-devices` | register_device, list_devices, unpair_device | — |
| `peloton` | list_workouts | `PELOTON_USERNAME`, `PELOTON_PASSWORD` |
| `permission-model` | request_approval, list_pending, approve, deny | — |
| `personal-feed` | publish_post, list_posts | — |
| `philips-hue` | list_lights, set_light | `HUE_BRIDGE_IP`, `HUE_USERNAME` |
| `places-search` | search_places | `GOOGLE_MAPS_API_KEY` |
| `plaid` | sandbox_connect, get_balances | `PLAID_CLIENT_ID`, `PLAID_SECRET` |
| `podcast` | search_podcasts, search_episodes | — |
| `printify` | list_shops, list_products | `PRINTIFY_API_TOKEN` |
| `quickbooks` | list_customers, run_query | `QUICKBOOKS_ACCESS_TOKEN`, `QUICKBOOKS_REALM_ID` |
| `secure-vault` | store_secret, get_secret, delete_secret, list_secrets | — |
| `self-awareness` | get_runtime_info, describe_skill | — |
| `share-ideas` | publish_idea | — |
| `shopify` | list_products, list_orders | `SHOPIFY_STORE`, `SHOPIFY_ADMIN_TOKEN` |
| `shopping` | search_products | `SERPER_API_KEY` |
| `skill-creator` | scaffold_skill | — |
| `slack` | list_channels, read_channel, send_message | `SLACK_BOT_TOKEN` |
| `social-content-performance` | account_insights, media_insights | `INSTAGRAM_ACCESS_TOKEN` |
| `spotify` | search, get_playlists, play, pause | `SPOTIFY_ACCESS_TOKEN` |
| `stripe` | list_customers, list_invoices, create_payment_link | `STRIPE_SECRET_KEY` |
| `subscription-status` | get_status | — |
| `tailscale` | list_devices | `TAILSCALE_API_KEY`, `TAILSCALE_TAILNET` |
| `tessie` | list_vehicles, get_state | `TESSIE_API_TOKEN` |
| `threads` | get_profile, post_text | `THREADS_ACCESS_TOKEN` |
| `threads-messages` | list_replies, get_conversation | `THREADS_ACCESS_TOKEN` |
| `ticketmaster` | search_events | `TICKETMASTER_API_KEY` |
| `todoist` | list_tasks, create_task | `TODOIST_API_TOKEN` |
| `travel-planning` | build_itinerary | — |
| `tts` | synthesize, list_voices | `ELEVENLABS_API_KEY` |
| `vercel` | list_projects, list_deployments | `VERCEL_TOKEN` |
| `voice-calls` | list_calls, make_call | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` |
| `voice-design` | design_voice | `ELEVENLABS_API_KEY` |
| `voice-selector` | list_voices | `ELEVENLABS_API_KEY` |
| `wallet` | get_state, connect, add_payment_method, list_payment_methods | — |
| `wearable-device-skills` | discover | — |
| `wearables-comms` | queue_notification, list_outbox | — |
| `wide-research` | research | `SERPER_API_KEY` |
| `withings` | get_body_measures | `WITHINGS_ACCESS_TOKEN` |
| `zapier` | trigger_zap | `ZAPIER_WEBHOOK_URL` |
| `zoom` | list_meetings, create_meeting | `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID` |

**94 implemented drivers.** Catalog-only stubs (3): `lovable`, `muse-early-access`, `replit` — no public API exists, so they return an honest `driver_not_implemented` error instead of fake data. `lovable`/`replit` document a GitHub-sync workaround in their SKILL.md.

Each driver module documents its own setup steps in `SETUP_HELP`.

## Calling a tool

Every executable action is its own MCP tool named `<skill>_<action>` with
flat, inlined parameters — there is no opaque `{ action, params }` envelope.
Control arguments (`confirm`, `approval_id`, `idempotency_key`) are popped
by the server; everything else is validated against the action's schema.

Read action:

```json
{ "tool": "github_search_repositories",
  "arguments": { "query": "mcp server language:python", "per_page": 3 } }
```

Write action (`communication` risk → needs a real approval, not just confirm):

```json
{ "tool": "permission_model_request_approval",
  "arguments": { "skill": "slack", "action": "send_message",
                 "params": { "channel_id": "C012AB345CD", "text": "Hello!" } } }
// → { "approval_id": "apr_..." }
// human approves, then:
{ "tool": "slack_send_message",
  "arguments": { "channel_id": "C012AB345CD", "text": "Hello!" },
  "approval_id": "apr_..." }
```

Tool names are unambiguous: `split_tool_name` resolves `<skill>_<action>`
with longest-skill-prefix-wins, and the validator fails the build on any
tool-name collision.

Without an approval, strict-risk actions raise `approval_required` — carrying the pending `approval_id` and a non-secret params preview.

## Tests (the proof)

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

What the suite proves:
1. All **97 skills** load from the catalog with **210 valid, typed MCP tool schemas**.
2. `github_search_repositories` performs a **live** `api.github.com` call.
3. Missing credentials → structured `credentials_missing` (honest, never fake).
4. Strict-risk write without approval → `approval_required` (approval engine enforced).
5. Full MCP server boots over **stdio**, serves all tools, executes a live call.
6. Audit log, idempotency keys, secret redaction, and SQL guardrails verified.

## Adding a driver

1. Copy `skillhub/skills/github.py` as your template.
2. Set `SKILL`, `REQUIRED_ENV`, `SETUP_HELP`, and `ACTIONS`.
3. If the skill name contains a hyphen, add it to `MODULE_OVERRIDES` in `registry.py`.
4. Add tests in `tests/test_runtime.py` and run the suite.

## Design notes

- `skillhub/errors.py` — every failure is a machine-readable dict.
- `skillhub/http.py` — shared async HTTP with upstream-error mapping and
  explicit proxy handling (works around an httpx IPv6 `no_proxy` parsing bug).
- `skillhub/registry.py` — discovers skills from `skillhub/catalog/*/SKILL.md`
  frontmatter, so the tool surface always matches the catalog.
- `skillhub/server.py` — MCP server over stdio (works with Claude Desktop
  and any MCP client).

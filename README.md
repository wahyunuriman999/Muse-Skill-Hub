<p align="center">
  <img src="assets/avatar.png" alt="Muse" width="180">
</p>

# Muse Skill Hub

> An open, LLM-agnostic capability runtime for AI agents. Define capabilities once. Discover them dynamically. Execute them through typed tools. Enforce permissions at runtime. Keep failures honest. Created by **Wahyu Nur Iman**.

## ⚡ Executable Runtime

<!-- METRICS:START -->
_Generated from registry + test suite — do not hand-edit. Run `python tools/sync_readme.py`._

**Version 2.3.0** · **97 skills** · **96 executable drivers** (1 honest stubs) · **222 MCP tools** · **309 passing tests**
<!-- METRICS:END -->

**Evidence honesty**: of the 96 executable drivers, 2 are live-tested against real provider servers (`github`, `podcast`), 3 have mock-contract tests (`stripe`, `lovable`, `replit`), and 91 are structural (real code, provider handshake is the operator's step). Full per-driver matrix: [`certification/PROVIDER_MATRIX.md`](certification/PROVIDER_MATRIX.md) (generated — do not hand-edit).

This repo is no longer just a catalog — it ships a **real MCP server**
exposing every action as its own typed tool (e.g. `github_search_repositories`,
with full JSON schemas — no opaque `params` blob). Skills are backed by real,
executable drivers; a few remain honest catalog-only stubs (structured
`driver_not_implemented` — never fake data):

```bash
cd runtime && pip install -r requirements.txt && python -m skillhub.server
```

- **94 real drivers** across three kinds:
  - *Third-party APIs* (62): `github`, `slack`, `stripe`, `shopify`, `linear`, `vercel`, `asana`, `notion`, `todoist`, `places-search`, `zoom`, `gmail`, `google-calendar`, `google-sheets`, `google-drive`, `spotify`, `instagram`, `meta-threads`, `threads`, `facebook`, `dropbox`, `ticketmaster`, `image-search`, `flightaware`, `box`, `calendly`, `canva`, `duffel`, `figma`, `ghl`, `klaviyo`, `meta-ads`, `plaid` (sandbox), `printify`, `quickbooks`, `tts`, `voice-design`, `voice-selector`, `voice-calls`, `zapier`, `outlook-calendar`, `outlook-mail`, `outlook-contacts`, `google-contacts`, `google-docs`, `google-forms`, `google-slides`, `google-tasks`, `messenger`, `instagram-messages`, `threads-messages`, `withings`, `tailscale`, `tessie`, `peloton`, `philips-hue`, `podcast`, `shopping`, `wide-research`, `social-content-performance`, `evernote`, `healthex` (MCP passthrough), `granola`, `generate_podcast` (needs ElevenLabs key for TTS)
  - *Local reference implementations* (32): `secure-vault` (encrypted), `permission-model`, `personal-feed`, `idea-management`, `goals`, `share-ideas`, `agent-library`, `connector-management`, `paired-devices`, `data-control`, `messaging-channels`, `wallet`, `apple-healthkit` + `google-health-connect` (local export readers), `device-data`, `media-library`, `forget`, `self-awareness`, `skill-creator`, `function-health`, `travel-planning`, `muse_db` (SQLite), `muse-feedback`, `subscription-status`, `wearable-device-skills`, `wearables-comms`, `booking` (router), `opentable` (deep links), `facebook-cli` (passthrough), `magic-moment` (local ffmpeg)
  - *Catalog-only stubs* (3): `lovable`, `muse-early-access`, `replit` — no public API exists (or it is an internal-only program); documented honestly instead of faked, with workarounds where one exists
- **MCP tools** (per-action, fully typed) + `skillhub_search_capabilities` for dynamic capability discovery (counts in the metrics block above)
- **Approval engine** — write actions need approval; `sensitive`/`destructive`/`communication`/`financial`/`account`/`device` risks require a real `approval_id` (bound to exact skill/action/params, single-use, 10-min TTL). Bare `confirm=true` only suffices for plain `write` risk
- **Policy engine** — risk-based allow/approval_required/deny with per-action classification and custom policy files
- **Audit log** — every execution recorded (request_id, actor, risk, params hash, approval_id, duration); secrets never logged raw; query via `function-health query_audit_log`
- **Idempotency** — `idempotency_key` on write actions: repeats return the first result instead of re-executing
- **Credential manager** — env → local file → encrypted vault; `ref:vault:<name>` references resolve server-side so secret values never reach the LLM
- **Hardened HTTP layer** — persistent connection pooling, retry with exponential backoff + `Retry-After`, `X-Request-ID` correlation, structured 429/5xx mapping
- **Skill manifests** — `runtime/skillhub/catalog/<name>/manifest.yaml` is the machine-readable contract; `skillhub validate` runs the conformance test (schemas, risk, auth, manifest/driver/SKILL.md drift, secret scan)
- **Passing tests** (count in the metrics block above), including live `api.github.com` calls, an end-to-end MCP stdio session with per-action tools, approval-lifecycle/idempotency/audit/security tests, and credential-error coverage for every API driver

### What's new in v2.2.0 (concurrency + crash hardening)

- **Cross-platform file locking** — new `skillhub.filelock` module (`fcntl` on Unix, `msvcrt` on Windows); no more top-level `import fcntl`, so the runtime imports cleanly on Windows
- **Crash-atomic stores** — every read-modify-write cycle (`locked_json`, credential store) now holds a *separate* `<name>.lock` file and writes back via tmp + fsync + `os.replace`: atomic against concurrency *and* crashes
- **OAuth single-flight refresh** — the check → refresh → persist cycle runs under the store lock with double-checked expiry; 20 concurrent workers on an expired token produce exactly 1 refresh request
- **Fail-closed credential store** — a corrupt/undecryptable `credentials.enc` raises `CredentialStoreCorruptError` (with a `.corrupt` backup) instead of silently looking like "no credentials"
- **Approval privacy** — the approval store no longer persists raw params; only `params_hash` + a redacted preview. Execution re-supplies params and `consume()` verifies them against the hash
- **Real JSON Schema** — validation now runs on the standard `jsonschema` library (Draft 2020-12, full vocabulary: `$ref`, `if`/`then`/`else`, `dependentRequired`, …) with format checking; `skillhub validate` lints every action schema
- **Declared dependencies** — `cryptography` and `jsonschema` are now official dependencies (they were already required at runtime)
- **Generated README metrics** — `runtime/tools/sync_readme.py` regenerates the metrics block from the registry + test suite; a test fails if the README drifts
- **Multi-process race tests** — approval consumption and idempotency reservation are now proven with 20 *processes* (not just threads), matching the documented guarantee

### What's new in v2.1.0 (security hardening)

- **Atomic approval consumption** — approval approve/consume transitions happen inside a locked critical section, so concurrent workers can't double-spend one approval (proven by a 20-thread race test)
- **Atomic idempotency** — `PENDING → SUCCEEDED | FAILED → CONFLICT` reservation happens *before* side effects; concurrent duplicates see `pending` and never re-execute; failed records allow exactly one reclaim
- **Honest naming** — `idempotent` renamed to `supports_idempotency_key`: the runtime supports dedup keys, it does not claim mathematical idempotence of the underlying API
- **Output contracts** — handler results are validated against each action's `output_schema` before success is committed; violations never get cached
- **Real JSON-Schema validation** (v2.2.0: standard `jsonschema` library, Draft 2020-12) — strict by default (unknown params rejected, like MCP's `additionalProperties: false`)
- **Credential scopes** — actions declare `required_scopes` (Gmail/Outlook/Google Workspace drivers); mismatches are blocked, unknown scopes are allowed but marked `unverified` in audit
- **Encrypted credential store** — local credentials now live in an encrypted `credentials.enc` (Fernet, secure-vault key); the old plaintext fallback is gone, legacy files are migrated and deleted
- **OAuth refresh manager** — encrypted access/refresh tokens with auto-refresh before expiry and rotation persistence
- **Audit hash chain** — every event carries `prev_hash`/`event_hash`; `python -m skillhub.cli audit-verify` detects tampering (tamper-evident, not tamper-proof)
- **TF-IDF capability discovery** — `skillhub_search_capabilities` now ranks by lexical relevance instead of substring matching
- **Provider mock harness** — `SKILLHUB_MOCK=1` routes `api_request` to canned responders; mock contract tests for GitHub and Stripe assert request shapes and auth flow without network
- **SQL hardening** — `muse_db` strips comments/strings before keyword scanning, runs reads on a read-only SQLite connection, and enforces single statements
- **Zero doc warnings** — all 178 missing action docs generated; `skillhub validate` passes clean
- **Passing tests** (count in the metrics block above; was 67 in v1.5.0), including 20-thread concurrency races, scope mismatches, encrypted-store migration, OAuth refresh, audit tampering, and provider contracts

**Security model (honest):** this is a trusted, local, single-user MCP runtime. Encryption protects against casual disk exposure, not against malware or same-user attackers. `actor` is a local session label, not authentication. Multi-user tenant isolation, distributed exactly-once, and workflow/saga engines remain out of scope (see `specs/`).

See [`runtime/README.md`](runtime/README.md) for setup, driver docs, and how to add your own driver. Specs live in [`specs/`](specs/) (manifest, error contract, approval protocol).

---
## About this repo

This repo contains a **catalog** of all of Muse's skills/capabilities (Muse is Meta's personal AI agent).
The goal is an open reference: what Muse can do, what the patterns are, and inspiration for building similar capabilities in other AIs/LLMs.

**Important note:** This file only contains high-level lists and descriptions, not raw internal files. Muse's real skills run on a specialized runtime (MCP servers, OAuth, custom CLIs, etc.), so just reading this list won't automatically make another AI 99.9% like Muse — but it can be a very useful blueprint.

Total documented skills: **97**

## Universal Skills (Usable by Any LLM) 🌐

Each skill now has **two files**:
- `runtime/skillhub/catalog/<name>/README.md` — Human-readable documentation (what it does, when to use)
- `runtime/skillhub/catalog/<name>/SKILL.md` — **Universal skill definition** in open format (frontmatter + instructions) that any LLM can load

See **[USAGE.md](USAGE.md)** for how to use these with GPT, Claude, Gemini, Llama, LangChain, etc.

**Quick start for any LLM:**
```python
# Option 1: Paste into system prompt
with open('runtime/skillhub/catalog/github/SKILL.md') as f:
    skill = f.read()
# Add to your LLM's context

# Option 2: LangChain
from langchain.tools import Tool
tool = Tool(name="github", description="...", func=your_impl)
```

## Skill List

| Skill | Title | Description |
|-------|-------|-------------|
| `agent-library` | Agent Library | Manage the user's file library: uploads, generated artifacts, expiring public share links, and the media collection. |
| `apple-healthkit` | Apple Health | The user's synced Apple Health (HealthKit) data: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts. |
| `asana` | asana | Manage Asana work: create and list tasks, assign owners, set due dates, organize projects, and track team progress. |
| `booking` | booking | Primary entry point for direct flight, hotel, restaurant, or event-ticket transactions and for bounded live availability checks delegated by Travel Planning. Always use before provider-specific skills |
| `box` | box | Search, read, upload, download, move, rename, delete, restore, and share Box content; manage comments and metadata. |
| `calendly` | calendly | View Calendly events and event types, and manage scheduling data using the Calendly CLI. |
| `canva` | canva | Design with Canva: create and edit designs and presentations, manage brand assets and folders, and generate share links. |
| `connector-management` | Connector Management | Manage third-party service connectors: check connection status and scopes, guide OAuth connect flows, and disconnect services. |
| `data-control` | Data Control | Handle user data rights: explain data collection and use, export chats and files, delete data on request, manage training opt-outs. |
| `device-data` | Device Data | Read cached contacts and calendar events from Muse storage. Delete Muse's local copy of either source without modifying paired devices. |
| `dropbox` | dropbox | Manage Dropbox storage: upload and download files, create share links, organize folders, and check space usage. |
| `duffel` | duffel | Use Duffel to search, book, pay for, or manage flights. Use Duffel to monitor an already booked flight's fare when the user directly asks for ongoing price monitoring. |
| `evernote` | evernote | Read and create notes through Evernote's official MCP server. |
| `facebook` | Facebook | Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public event |
| `facebook-cli` | Facebook | Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public event |
| `figma` | figma | Work with Figma: read files, pages, frames and components, export assets, and manage design projects. |
| `flightaware` | FlightAware AeroAPI | Use for questions about a specific flight’s departure or arrival time, including “when’s my flight?” and confirmation of remembered times, plus flight status, delays, and cancellations. Verify the exa |
| `forget` | forget | Remove a personal fact, preference, relationship detail, topic, or prior event from Muse's active memory and stop existing copies or automations from bringing it back. Use for explicit requests such a |
| `function-health` | function-health | Retrieve lab biomarker results and clinician notes from Function Health. |
| `generate_podcast` | generate_podcast | Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts. |
| `ghl` | ghl | Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog. |
| `github` | GitHub | Search and work with the user's GitHub repositories through GitHub's official MCP server. |
| `gmail` | gmail | Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments. |
| `goals` | goals | Guidance for helping users create and accomplish goals. Read it before you create a goal for the user when no goal-creation contract is in context, and whenever you help with an existing goal. A Goals |
| `google-calendar` | google-calendar | Work with the user's Google Calendar: agenda views, event details, and scheduling changes. |
| `google-contacts` | google-contacts | Search, view, create, update, and delete the user's Google Contacts. |
| `google-docs` | google-docs | Read, create, and edit the user's Google Docs. |
| `google-drive` | google-drive | Work with the user's Google Drive: files, folders, uploads, downloads, and sharing. |
| `google-forms` | google-forms | Read, create, and update the user's Google Forms, and read responses. |
| `google-health-connect` | Health Connect | The user's synced Google Health Connect data from their Android device: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts. |
| `google-sheets` | google-sheets | Read, write, and manage the user's Google Sheets. |
| `google-slides` | google-slides | Read, create, and edit the user's Google Slides presentations. |
| `google-tasks` | google-tasks | Manage the user's Google Tasks: lists, task details, creation, updates, and completion. |
| `granola` | granola | Search and read Granola meeting notes and transcripts through Granola's official public API (public-api.granola.ai). Requires a Granola API key (GRANOLA_API_KEY). |
| `healthex` | HealthEx | Use to connect HealthEx and ask questions about your medications, lab results, and other health records. |
| `idea-management` | Idea Management | Manage the Ideas tab: idea cards the agent can run, dismissing ideas, and explaining why an idea appeared or disappeared. |
| `image-search` | image-search | Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person. |
| `instagram` | instagram | Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile d |
| `instagram-messages` | instagram-messages | Use this to interact with the user's Instagram messages. Read inboxes, threads, top recipients, filtered inbox views, DM search results, and send messages through `instagram-messages-cli`. |
| `klaviyo` | klaviyo | Run Klaviyo email/SMS marketing: manage lists and segments, build campaigns and flows, and edit templates. |
| `linear` | linear | Track engineering work in Linear: create and list issues, set priorities, manage cycles, and follow project status. |
| `lovable` | lovable | Lovable AI app builder. No public API exists, so this skill is catalog-only: the honest workaround is Lovable's GitHub sync, then operate on the code with the github skill. |
| `magic-moment` | magic-moment | Turn talking-head video footage into shareable short clips. The hosted AI-highlight feature has no public API, so this skill ships an honest local ffmpeg implementation: cut clips, burn in SRT captions, reframe to vertical 9:16. |
| `media-library` | media-library | Search and inspect the user's photo library, including connected device galleries. Use for photo requests and whenever a photo could ground or personalize a response; lookups of uploaded photos are ch |
| `messaging-channels` | Messaging Channels | Work across connected messaging providers (e.g. WhatsApp): check connection status, read side chats, send messages with approval. |
| `messenger` | Messenger | Work with the user's Messenger account: read call history; read and search contacts; read, search, and summarize conversations; send, react to, unsend, or edit messages; and message Marketplace listin |
| `meta-ads` | Meta Ads | Create, write, or manage Meta ads and assets: ad copy, campaigns, spend, reports, audiences, catalogs, product feeds, feed refresh schedules, experiments, and policy. Always load for any request to cr |
| `meta-threads` | meta-threads | Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish pos |
| `muse-early-access` | Muse early access | Use for questions about Muse's general early access program, requests to join it, checking or withdrawing a join request, and admission updates. |
| `muse-feedback` | Muse feedback | Use for feedback and feature requests to the Muse team. Whenever your response tells the user you can't do a specific thing they wanted, or accepts them giving up on one, offer once to file feedback i |
| `muse_db` | muse_db | Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built product tools do not expose the needed state. |
| `notion` | notion | Search, read, create, and update Notion pages via the Notion MCP. |
| `opentable` | OpenTable | Find restaurants on OpenTable, check availability, and make, change, or cancel reservations. Use for restaurant booking and live reservation data. |
| `outlook-calendar` | outlook-calendar | View, create, update, and delete events in the user's Outlook Calendar. |
| `outlook-contacts` | outlook-contacts | List, search, create, update, and delete contacts in the user's Outlook account. |
| `outlook-mail` | outlook-mail | Read, search, send, reply to, and delete messages in the user's Outlook Mail. |
| `paired-devices` | Paired Devices | Manage the user's paired devices: list devices, run commands, pull data such as location, and unpair devices. |
| `peloton` | peloton | Connect to Peloton to browse fitness classes, check schedules, and book workouts. |
| `permission-model` | Permission Model | Work with the runtime permission system: list pending requests, explain the access each grants, respect approve/deny decisions. |
| `personal-feed` | Personal Feed | Manage the user's personal Feed: editorial posts written on a schedule, the feed brief, regenerating or removing posts. |
| `philips-hue` | philips-hue | Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2. |
| `places-search` | Places Search | Find, compare, and share details on physical places near the user or in a specified area, including restaurants, cafes, bars, hotels, parks, attractions, shops, and businesses with local services. Not |
| `plaid` | Finances (Plaid) | Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring transactions, liabilities, and investments. |
| `podcast` | podcast | Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts. |
| `printify` | printify | Use Printify to browse catalog data, manage shops and products, and review or create orders. |
| `quickbooks` | quickbooks | Read and manage the user's QuickBooks business through Intuit's official MCP server, including reports, invoices, customers, products, payment links, sales settings, and industry benchmarks. |
| `replit` | replit | Replit cloud IDE. Replit's public REST API is deprecated and its replacement is unreleased, so this skill is catalog-only: the honest workaround is pushing the Repl to GitHub, then operating on the code with the github skill. |
| `secure-vault` | Secure Vault | Handle credentials securely: collect passwords, API keys, and tokens only through secure entry UI, never in chat. |
| `self-awareness` | self-awareness | Ground self-referential answers in the agent's actual filesystem. Use when the user asks who the agent is, what it can do, what it knows, what it remembers, what it has built, what services are connec |
| `share-ideas` | Share ideas | Publish a portable Idea card from the Ideas tab — only after the user explicitly asks to publish it. |
| `shopify` | shopify | Manage a Shopify store: list and update products, orders, customers, inventory levels, and discount codes. |
| `shopping` | shopping | Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, includin |
| `skill-creator` | skill-creator | Create or update a workspace skill: its description, structure, instructions, and supporting files. |
| `slack` | slack | Work with Slack: list channels, read and send messages, manage threads and reactions, and search history. |
| `social-content-performance` | Social Content Performance | Analyze the user's own Instagram account and post performance using linked-account analytics. |
| `spotify` | spotify | Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify. |
| `stripe` | stripe | Handle Stripe payments: create payment links and checkout sessions, manage customers, subscriptions, invoices, and refunds. |
| `subscription-status` | subscription-status | Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available plans and prices, or verify information that references the Muse subscription. |
| `tailscale` | Tailscale | Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and reach private machines through the TCP tunnel proxy. Read for Tailscale, VPN, MagicDNS, network egres |
| `tessie` | tessie | Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints. |
| `threads` | threads | Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish pos |
| `threads-messages` | threads-messages | Use this to interact with the user's Threads messages: read inboxes and message threads, and send messages through `threads-messages-cli`. |
| `ticketmaster` | ticketmaster | Search Ticketmaster events and seats with pricing. Returns Buy-now links to Ticketmaster checkout; it cannot complete a purchase itself. |
| `todoist` | todoist | Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's official MCP server. |
| `travel-planning` | travel-planning | Use this skill when an active or proposed trip needs planning, logistics, feasibility, entry or transit checks, itinerary work, or investigation of an airport process, immigration, ground transport, a |
| `tts` | tts | Turn supplied text into spoken audio, single or multi-speaker. For composed audio content (a podcast, briefing, or narrated summary), use podcast. |
| `vercel` | vercel | Deploy with Vercel: list projects and deployments, promote to production, manage domains and environment variables. |
| `voice-calls` | voice-calls | Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow. |
| `voice-design` | voice-design | Choose or design a speaking voice when the user asks for a new, different, custom, invented, or generated voice, or restore the voice used immediately before the current one. |
| `voice-selector` | voice-selector | Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow. |
| `wallet` | Wallet | Coordinate payments: check wallet connection state, use saved payment methods through secure provider pages, run purchase review and approval. |
| `wearable-device-skills` | Wearable Device Skills | Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published by a paired phone or wearable, including device controls, app actions, camera or media actions, and s |
| `wearables-comms` | Wearables Calls and Messages | Handle calls and messages through connected wearables: read notifications, place and answer calls, and send quick replies. |
| `wide-research` | wide-research | Use when the user needs broad parallel research across many independent inputs with a shared output schema. |
| `withings` | withings | Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, and intraday data. |
| `zapier` | zapier | Connect Muse to actions across apps through Zapier's official MCP server. |
| `zoom` | zoom | Manage Zoom: schedule and list meetings, fetch recordings, and manage meeting settings. |

## How to use

- Browse the table above to see capability patterns.
- Each Muse skill follows a pattern: **clear purpose, structured input, and safe actions** (read vs write separated).
- If you want to build a Muse-like AI, copy the pattern: define skills as instructions + input schema, not just freeform prompts.

## Community skills

Skills from other authors, in the same open `SKILL.md` format, that Muse-style agents can load.

| Skill | Description |
|-------|-------------|
| [sparkbtcbot](https://github.com/echennells/sparkbtcbot) | Give an agent its own self-custodial Bitcoin wallet on the Spark L2: receive and pay over Lightning and Spark, pay L402 paywalls, move BTKN tokens, and buy gift cards with a confirm-before-buy step. Encrypted seed, amount and fee caps, a daily spend budget, an outbound allowlist, payment dedup, and a unilateral-exit backup. MIT. [Demo video](https://x.com/sparkbtcbot/status/2104971010475012423) |

## Contributing

PRs and issues are welcome. If you adapt these skills for other LLMs, share it here.

## License

This project is licensed under the **GNU Affero General Public License v3.0**
(AGPL-3.0-only) — see [LICENSE](LICENSE) for the full text.

In short: you may use, study, modify, and share this work, but any modified
version you distribute (including over a network) must remain open-source
under the same license, with copyright and attribution notices intact.

---
*Copyright © 2026 Wahyu Nur Iman.*

# Muse Skill Hub

> Katalog kemampuan Muse — dibuat agar AI & LLM lain bisa memahami pola kemampuan Muse. Dibuat oleh Wahyu.

## Tentang repo ini

Repo ini berisi **katalog** dari semua skill/kemampuan Muse (asisten AI pribadi dari Meta).
Tujuannya sebagai referensi terbuka: apa saja yang bisa dilakukan Muse, bagaimana polanya, dan inspirasi untuk membangun kemampuan serupa di AI/LLM lain.

**Catatan penting:** File ini hanya berisi daftar dan deskripsi tingkat tinggi, bukan file internal mentah. Skill asli Muse berjalan di atas runtime khusus (MCP server, OAuth, CLI khusus, dll), jadi sekadar membaca daftar ini tidak otomatis membuat AI lain menjadi 99,9% seperti Muse — tapi bisa jadi blueprint yang sangat berguna.

Total skill terdokumentasi: **87**

## Daftar Skill

| Skill | Judul | Deskripsi |
|-------|-------|-----------|
| `apple-healthkit` | Apple Health | The user's synced Apple Health (HealthKit) data: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts. |
| `asana` | asana |  |
| `booking` | booking | Primary entry point for direct flight, hotel, restaurant, or event-ticket transactions and for bounded live availability checks delegated by Travel Planning. Always use before provider-specific skills |
| `box` | box | Search, read, upload, download, move, rename, delete, restore, and share Box content; manage comments and metadata. |
| `calendly` | calendly | View Calendly events and event types, and manage scheduling data using the Calendly CLI. |
| `canva` | canva |  |
| `device-data` | Device Data | Read cached contacts and calendar events from Muse storage. Delete Muse's local copy of either source without modifying paired devices. |
| `dropbox` | dropbox |  |
| `duffel` | duffel | Use Duffel to search, book, pay for, or manage flights. Use Duffel to monitor an already booked flight's fare when the user directly asks for ongoing price monitoring. |
| `evernote` | evernote | Read and create notes through Evernote's official MCP server. |
| `facebook` | Facebook | Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public event |
| `facebook-cli` | Facebook | Use when the user provides a Facebook URL or asks to read personal posts, comments, reactions, friends, timelines, profiles, stories, feeds, groups, events, or saved items, or to discover public event |
| `figma` | figma |  |
| `flightaware` | FlightAware AeroAPI | Use for questions about a specific flight’s departure or arrival time, including “when’s my flight?” and confirmation of remembered times, plus flight status, delays, and cancellations. Verify the exa |
| `forget` | forget | Remove a personal fact, preference, relationship detail, topic, or prior event from Muse's active memory and stop existing copies or automations from bringing it back. Use for explicit requests such a |
| `function-health` | function_health | Retrieve lab biomarker results and clinician notes from Function Health. |
| `generate_podcast` | generate_podcast | Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts. |
| `ghl` | ghl | Use HighLevel contacts, pipelines, appointments, messages, and its broader operation catalog. |
| `github` | GitHub | Search and work with the user's GitHub repositories through GitHub's official MCP server. |
| `gmail` | gmail | Work with the user's Gmail: search, read threads, draft, send, reply, forward, unsubscribe from mailing lists, manage labels, and open attachments. |
| `goals` | goals | Guidance for helping users create and accomplish goals. Read it before you create a goal for the user when no goal-creation contract is in context, and whenever you help with an existing goal. A Goals |
| `google-calendar` | google_calendar | Work with the user's Google Calendar: agenda views, event details, and scheduling changes. |
| `google-contacts` | google_contacts | Search, view, create, update, and delete the user's Google Contacts. |
| `google-docs` | google_docs | Read, create, and edit the user's Google Docs. |
| `google-drive` | google_drive | Work with the user's Google Drive: files, folders, uploads, downloads, and sharing. |
| `google-forms` | google_forms | Read, create, and update the user's Google Forms, and read responses. |
| `google-health-connect` | Health Connect | The user's synced Google Health Connect data from their Android device: daily metrics (steps, distance, calories, heart rate, HRV, VO2max), sleep sessions (stages, quality, efficiency), and workouts. |
| `google-sheets` | google_sheets | Read, write, and manage the user's Google Sheets. |
| `google-slides` | google_slides | Read, create, and edit the user's Google Slides presentations. |
| `google-tasks` | google_tasks | Manage the user's Google Tasks: lists, task details, creation, updates, and completion. |
| `granola` | granola | Search and read Granola meeting notes and transcripts through Granola's OAuth-backed MCP server. |
| `healthex` | HealthEx | Use to connect HealthEx and ask questions about your medications, lab results, and other health records. |
| `image-search` | image_search | Search the web by text query for image URLs and source pages for feeds, artifacts, and visual references. Does not identify a supplied image or person. |
| `instagram` | instagram | Read Instagram profiles, followers, posts, comments, likes, stories, feed, saved content, and account insights. Answer questions about posts, reels, and Instagram links. Manage interests and profile d |
| `instagram-messages` | instagram_messages | Use this to interact with the user's Instagram messages. Read inboxes, threads, top recipients, filtered inbox views, DM search results, and send messages through `instagram-messages-cli`. |
| `klaviyo` | klaviyo |  |
| `linear` | linear |  |
| `lovable` | lovable |  |
| `magic-moment` | magic-moment |  |
| `media-library` | media_library | Search and inspect the user's photo library, including connected device galleries. Use for photo requests and whenever a photo could ground or personalize a response; lookups of uploaded photos are ch |
| `messenger` | Messenger | Work with the user's Messenger account: read call history; read and search contacts; read, search, and summarize conversations; send, react to, unsend, or edit messages; and message Marketplace listin |
| `meta-ads` | Meta Ads | Create, write, or manage Meta ads and assets: ad copy, campaigns, spend, reports, audiences, catalogs, product feeds, feed refresh schedules, experiments, and policy. Always load for any request to cr |
| `meta-threads` | threads | Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish pos |
| `muse-early-access` | Muse early access | Use for questions about Muse's general early access program, requests to join it, checking or withdrawing a join request, and admission updates. |
| `muse-feedback` | Muse feedback | Use for feedback and feature requests to the Muse team. Whenever your response tells the user you can't do a specific thing they wanted, or accepts them giving up on one, offer once to file feedback i |
| `muse_db` | muse_db | Inspect database-backed Muse records for diagnosis and cross-table tracing when purpose-built product tools do not expose the needed state. |
| `notion` | notion | Search, read, create, and update Notion pages via the Notion MCP. |
| `opentable` | OpenTable | Find restaurants on OpenTable, check availability, and make, change, or cancel reservations. Use for restaurant booking and live reservation data. |
| `outlook-calendar` | outlook_calendar | View, create, update, and delete events in the user's Outlook Calendar. |
| `outlook-contacts` | outlook_contacts | List, search, create, update, and delete contacts in the user's Outlook account. |
| `outlook-mail` | outlook_mail | Read, search, send, reply to, and delete messages in the user's Outlook Mail. |
| `peloton` | peloton | Connect to Peloton to browse fitness classes, check schedules, and book workouts. |
| `philips-hue` | philips_hue | Control Philips Hue smart lights, rooms, scenes, and devices via the Hue Remote API v2. |
| `places-search` | Places Search | Find, compare, and share details on physical places near the user or in a specified area, including restaurants, cafes, bars, hotels, parks, attractions, shops, and businesses with local services. Not |
| `plaid` | Finances (Plaid) | Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring transactions, liabilities, and investments. |
| `podcast` | generate_podcast | Compose and deliver audio content: a podcast episode, briefing, or narrated summary, with one or more voices, as an MP3. For reading supplied text aloud verbatim, use tts. |
| `printify` | printify | Use Printify to browse catalog data, manage shops and products, and review or create orders. |
| `quickbooks` | quickbooks | Read and manage the user's QuickBooks business through Intuit's official MCP server, including reports, invoices, customers, products, payment links, sales settings, and industry benchmarks. |
| `replit` | replit | Read, create, update, and publish apps through Replit's official MCP server. |
| `self-awareness` | self_awareness | Ground self-referential answers in the agent's actual filesystem. Use when the user asks who the agent is, what it can do, what it knows, what it remembers, what it has built, what services are connec |
| `share-ideas` | Share ideas |  |
| `shopify` | shopify |  |
| `shopping` | shopping | Use for any product or shopping question: find, reverse image search, shopping Instagram/Marketplace links, buy, compare, or evaluate real products with prices, images, and product page URLs, includin |
| `skill-creator` | skill_creator | Create or update a workspace skill: its description, structure, instructions, and supporting files. |
| `slack` | slack |  |
| `social-content-performance` | Social Content Performance | Analyze the user's own Instagram account and post performance using linked-account analytics. |
| `spotify` | spotify | Discover, search, and manage Spotify music, podcasts, and playlists, including deleting shows or episodes you created with Save to Spotify. |
| `stripe` | stripe |  |
| `subscription-status` | subscription_status | Answer questions about the user's Muse subscription, plan, usage, tokens, reset timing, or available plans and prices, or verify information that references the Muse subscription. |
| `tailscale` | Tailscale | Set up Muse's built-in Tailscale connector, join a tailnet or Headscale network, check status, and reach private machines through the TCP tunnel proxy. Read for Tailscale, VPN, MagicDNS, network egres |
| `tessie` | tessie | Monitor a Tesla vehicle, inspect live state, and run explicit Tessie command endpoints. |
| `threads` | threads | Read and manage the user's Threads account: profile, posts, feed, saved posts, activity, insights, social graph, search, trends, and a specific post by URL or ID. Can tune feed ranking and publish pos |
| `threads-messages` | threads_messages | Use this to interact with the user's Threads messages: read inboxes and message threads, and send messages through `threads-messages-cli`. |
| `ticketmaster` | ticketmaster | Search Ticketmaster events and seats with pricing. Returns Buy-now links to Ticketmaster checkout; it cannot complete a purchase itself. |
| `todoist` | todoist | Read and manage Todoist tasks, projects, comments, labels, filters, and reminders through Todoist's official MCP server. |
| `travel-planning` | travel_planning | Use this skill when an active or proposed trip needs planning, logistics, feasibility, entry or transit checks, itinerary work, or investigation of an airport process, immigration, ground transport, a |
| `tts` | tts | Turn supplied text into spoken audio, single or multi-speaker. For composed audio content (a podcast, briefing, or narrated summary), use podcast. |
| `vercel` | vercel |  |
| `voice-calls` | voice_selector | Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow. |
| `voice-design` | voice_design | Choose or design a speaking voice when the user asks for a new, different, custom, invented, or generated voice, or restore the voice used immediately before the current one. |
| `voice-selector` | voice_selector | Provides the static system voice catalog used by Jarvis. It does not define a user-facing workflow. |
| `wearable-device-skills` | Wearable Device Skills | Use when the user asks to discover, inspect, or invoke an agentic capability dynamically published by a paired phone or wearable, including device controls, app actions, camera or media actions, and s |
| `wearables-comms` | Wearables Calls and Messages |  |
| `wide-research` | wide_research | Use when the user needs broad parallel research across many independent inputs with a shared output schema. |
| `withings` | withings | Use when linking Withings or reading Withings body measurements, activity, sleep, workout, heart, and intraday data. |
| `zapier` | zapier | Connect Muse to actions across apps through Zapier's official MCP server. |
| `zoom` | zoom |  |

## Cara pakai

- Jelajahi tabel di atas untuk melihat pola kemampuan.
- Setiap skill di Muse punya pola: **tujuan jelas, input terstruktur, dan aksi yang aman** (read vs write dipisah).
- Kalau mau bikin AI mirip Muse, tiru polanya: definisikan skill sebagai instruksi + skema input, bukan sekadar prompt bebas.

## Kontribusi

PR dan issue dipersilakan. Kalau kamu bikin adaptasi skill ini untuk LLM lain, share di sini.

---
*Dibuat dengan bantuan Muse — asisten AI pribadi Wahyu.*
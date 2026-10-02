# Live contract-test report

_Generated 2026-10-02 18:26 WIB. Read-only smoke calls against live provider APIs._

| Skill | Action | Tier | Status | Detail |
|---|---|---|---|---|
| podcast | search_podcasts | public | **PASS** | 414 ms |
| ticketmaster | — | — | **SKIP** | needs TICKETMASTER_API_KEY |
| github | search_repositories | keyed | **PASS** | 873 ms |
| stripe | — | — | **SKIP** | needs STRIPE_SECRET_KEY |
| lovable | — | — | **SKIP** | needs LOVABLE_API_KEY |
| replit | — | — | **SKIP** | needs REPLIT_API_KEY |
| granola | — | — | **SKIP** | needs GRANOLA_API_KEY |
| flightaware | — | — | **SKIP** | needs FLIGHTAWARE_API_KEY |
| asana | — | — | **SKIP** | read action needs params — manual spec |
| box | — | — | **SKIP** | needs BOX_ACCESS_TOKEN |
| calendly | — | — | **SKIP** | needs CALENDLY_API_TOKEN |
| canva | — | — | **SKIP** | needs CANVA_ACCESS_TOKEN |
| dropbox | — | — | **SKIP** | needs DROPBOX_ACCESS_TOKEN |
| duffel | — | — | **SKIP** | read action needs params — manual spec |
| facebook | — | — | **SKIP** | needs FACEBOOK_ACCESS_TOKEN |
| figma | — | — | **SKIP** | read action needs params — manual spec |
| ghl | — | — | **SKIP** | needs GHL_API_KEY |
| gmail | — | — | **SKIP** | needs GOOGLE_OAUTH_TOKEN |
| google-calendar | — | — | **SKIP** | needs GOOGLE_OAUTH_TOKEN |
| google-contacts | — | — | **SKIP** | needs GOOGLE_OAUTH_TOKEN |
| google-docs | — | — | **SKIP** | read action needs params — manual spec |
| google-drive | — | — | **SKIP** | needs GOOGLE_OAUTH_TOKEN |
| google-forms | — | — | **SKIP** | read action needs params — manual spec |
| google-sheets | — | — | **SKIP** | read action needs params — manual spec |
| google-slides | — | — | **SKIP** | read action needs params — manual spec |
| google-tasks | — | — | **SKIP** | needs GOOGLE_OAUTH_TOKEN |
| image-search | — | — | **SKIP** | read action needs params — manual spec |
| instagram | — | — | **SKIP** | needs INSTAGRAM_ACCESS_TOKEN |
| instagram-messages | — | — | **SKIP** | needs INSTAGRAM_PAGE_TOKEN |
| klaviyo | — | — | **SKIP** | needs KLAVIYO_API_KEY |
| linear | — | — | **SKIP** | needs LINEAR_API_KEY |
| messaging-channels | list_channels | keyed | **PASS** | 0 ms |
| messenger | — | — | **SKIP** | needs MESSENGER_PAGE_TOKEN |
| meta-ads | — | — | **SKIP** | needs META_ADS_ACCESS_TOKEN |
| meta-threads | — | — | **SKIP** | needs THREADS_ACCESS_TOKEN |
| notion | — | — | **SKIP** | read action needs params — manual spec |
| outlook-calendar | — | — | **SKIP** | needs MICROSOFT_ACCESS_TOKEN |
| outlook-contacts | — | — | **SKIP** | needs MICROSOFT_ACCESS_TOKEN |
| outlook-mail | — | — | **SKIP** | needs MICROSOFT_ACCESS_TOKEN |
| peloton | — | — | **SKIP** | needs PELOTON_USERNAME, PELOTON_PASSWORD |
| philips-hue | — | — | **SKIP** | needs HUE_BRIDGE_IP, HUE_USERNAME |
| places-search | — | — | **SKIP** | read action needs params — manual spec |
| plaid | — | — | **SKIP** | read action needs params — manual spec |
| printify | — | — | **SKIP** | needs PRINTIFY_API_TOKEN |
| quickbooks | — | — | **SKIP** | needs QUICKBOOKS_ACCESS_TOKEN, QUICKBOOKS_REALM_ID |
| shopify | — | — | **SKIP** | needs SHOPIFY_STORE, SHOPIFY_ADMIN_TOKEN |
| shopping | — | — | **SKIP** | read action needs params — manual spec |
| slack | — | — | **SKIP** | needs SLACK_BOT_TOKEN |
| social-content-performance | — | — | **SKIP** | needs INSTAGRAM_ACCESS_TOKEN |
| spotify | — | — | **SKIP** | needs SPOTIFY_ACCESS_TOKEN |
| tailscale | — | — | **SKIP** | needs TAILSCALE_API_KEY, TAILSCALE_TAILNET |
| tessie | — | — | **SKIP** | needs TESSIE_API_TOKEN |
| threads-messages | — | — | **SKIP** | read action needs params — manual spec |
| todoist | — | — | **SKIP** | needs TODOIST_API_TOKEN |
| tts | — | — | **SKIP** | needs ELEVENLABS_API_KEY |
| vercel | — | — | **SKIP** | needs VERCEL_TOKEN |
| voice-calls | — | — | **SKIP** | needs TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN |
| voice-design | — | — | **SKIP** | no read action — needs manual spec |
| voice-selector | — | — | **SKIP** | needs ELEVENLABS_API_KEY |
| wide-research | — | — | **SKIP** | read action needs params — manual spec |
| withings | — | — | **SKIP** | needs WITHINGS_ACCESS_TOKEN |
| zapier | — | — | **SKIP** | no read action — needs manual spec |
| zoom | — | — | **SKIP** | needs ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID |

**3 PASS · 60 SKIP · 0 FAIL** out of 63.

## Keys needed (one per SKIP)

- `BOX_ACCESS_TOKEN`
- `CALENDLY_API_TOKEN`
- `CANVA_ACCESS_TOKEN`
- `DROPBOX_ACCESS_TOKEN`
- `ELEVENLABS_API_KEY`
- `FACEBOOK_ACCESS_TOKEN`
- `FLIGHTAWARE_API_KEY`
- `GHL_API_KEY`
- `GOOGLE_OAUTH_TOKEN`
- `GRANOLA_API_KEY`
- `HUE_BRIDGE_IP, HUE_USERNAME`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_PAGE_TOKEN`
- `KLAVIYO_API_KEY`
- `LINEAR_API_KEY`
- `LOVABLE_API_KEY`
- `MESSENGER_PAGE_TOKEN`
- `META_ADS_ACCESS_TOKEN`
- `MICROSOFT_ACCESS_TOKEN`
- `PELOTON_USERNAME, PELOTON_PASSWORD`
- `PRINTIFY_API_TOKEN`
- `QUICKBOOKS_ACCESS_TOKEN, QUICKBOOKS_REALM_ID`
- `REPLIT_API_KEY`
- `SHOPIFY_STORE, SHOPIFY_ADMIN_TOKEN`
- `SLACK_BOT_TOKEN`
- `SPOTIFY_ACCESS_TOKEN`
- `STRIPE_SECRET_KEY`
- `TAILSCALE_API_KEY, TAILSCALE_TAILNET`
- `TESSIE_API_TOKEN`
- `THREADS_ACCESS_TOKEN`
- `TICKETMASTER_API_KEY`
- `TODOIST_API_TOKEN`
- `TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN`
- `VERCEL_TOKEN`
- `WITHINGS_ACCESS_TOKEN`
- `ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID`

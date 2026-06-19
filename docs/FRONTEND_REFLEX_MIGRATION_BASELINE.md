# Frontend Reflex Migration Baseline

Date: 2026-06-16  
Repository: `Hegehub/bitcoinbastion`  
Scope: audit and cutover planning only. No production switch, route replacement, Next.js deletion, Market dashboard removal, or backend domain rewrite was performed.

## 1. Executive summary

Bitcoin Bastion currently has three frontend/web surfaces:

1. **Next.js frontend** in `frontend/`: active public frontend with App Router routes, Trace pages, command palette, navigation, API clients, and Vitest/Playwright tests.
2. **FastAPI/Jinja Market dashboard** in `app/web/`: active server-rendered Market Intelligence / Market Time Machine dashboard and DTO endpoints mounted directly on the FastAPI app.
3. **Reflex frontend** in `reflex_frontend/`: present and partially scaffolded/implemented, not absent. It contains Reflex routes, services, state modules, safety helpers, Dockerfile, `pyproject.toml`, `uv.lock`, and tests, but this audit does **not** mark it as primary or parity-complete.

The migration must remain parity-controlled. Next.js and the FastAPI/Jinja Market dashboard must stay available until Reflex passes the cutover gates in this document.

High-risk blockers found:

- Required final console paths use `/console/*`, while current Next.js console-like routes are mostly `/dashboard/*`; some Reflex `/console/*` files exist but must be verified against production route parity.
- Required Market public route ownership is split: Next.js command palette points to Market paths, but the actual Market pages are owned by FastAPI/Jinja.
- Trace backend endpoints are mostly present, including `/api/v1/trace/lite/{address}`, `/api/v1/trace/address/{address}`, report, evidence, Proof Packet, and public summary endpoints. Trace remains a migration blocker until every required Reflex route, API call, warning, fallback, and forbidden-wording test passes.
- The requested Trace API contract includes `/api/v1/trace/report/{report_id}/utxo-hygiene` and `/dust-radar`; these exist in backend but are not currently called by the Next.js `apiClient`.
- `reflex_frontend/` already exists and must be audited as partial/experimental rather than generated from scratch in later prompts.
- Stale route files exist for `/products/*` and `/self-host/*`. Current nav/command-palette tests assert these are absent from main nav/palette, but the pages remain in the tree and should be treated as cleanup/archival decisions, not deletion targets yet.

Verification commands run for this audit are recorded in [Current tests and missing tests](#10-current-tests-and-missing-tests).

## 2. Current frontend surfaces

| Surface | Path | Status | Owns routes | Notes |
|---|---:|---|---|---|
| Next.js frontend | `frontend/` | Active legacy frontend until Reflex parity | `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[reportId]`, `/trace/[reportId]/proof-packet`, many legacy/product/self-host/dashboard routes | Uses Next.js 14, React, API clients in `frontend/services/`, tests in `frontend/tests/`. |
| FastAPI/Jinja web dashboard | `app/web/` | Active Market dashboard; keep during parity | `/market`, `/market-time-machine`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`, `/web/*` DTO/action endpoints | Mounted by `app.main`; templates under `app/web/templates/`; static assets under `app/web/static/`. |
| Reflex frontend | `reflex_frontend/` | Present; partial/experimental until proven otherwise | Contains route modules for public and console routes, including Trace/check/proof-packet/console modules | Already has `rxconfig.py`, `pyproject.toml`, `uv.lock`, `Dockerfile`, services/state/security/tests. It is not primary until cutover gates pass. |

Inspected required paths:

| Path | Exists? | Audit note |
|---|---:|---|
| `README.md` | Yes | Project overview/readiness context inspected for scope. |
| `docs/STATUS.md` | Yes | Status docs exist; must stay consistent with migration state. |
| `docs/PRODUCTION_READINESS.md` | Yes | Production readiness claims must not imply Reflex parity until proven. |
| `app/main.py` | Yes | Mounts API routers with `settings.api_prefix` and mounts Market web router without `/api/v1`. |
| `app/api/v1/public.py` | Yes | Public endpoints exist under `/api/v1/public/*`. |
| `app/api/v1/trace.py` | Yes | Trace endpoints exist under `/api/v1/trace/*`. |
| `app/web/routes_market.py` | Yes | FastAPI/Jinja Market owner and DTO/action endpoints. |
| `frontend/package.json` | Yes | Next.js 14 + Vitest/Playwright scripts. |
| `frontend/app/` | Yes | App Router route tree. |
| `frontend/components/` | Yes | Public, layout, Trace, command palette, navigation components. |
| `frontend/services/` | Yes | `api.ts`, `apiClient.ts`. |
| `frontend/tests/` | Yes | Vitest and Playwright coverage. |
| `deploy/` | Yes | Kubernetes/runtime deploy assets; no Reflex compose cutover proven by this audit. |
| `Makefile` | Yes | Repository commands; no production frontend cutover performed. |

## 3. Current route inventory

### 3.1 Actual Next.js route files found

Current Next.js App Router pages include:

- Public/core: `/`, `/platform`, `/developers`, `/developers/api`, `/developers/examples`, `/developers/webhooks`, `/developers/contributing`, `/developers/changelog`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[reportId]`, `/trace/[reportId]/proof-packet`.
- Trace extensions: `/trace/business`, `/trace/business/batch`, `/trace/business/policies`, `/trace/business/review`, `/trace/enterprise`, `/trace/enterprise/audit`, `/trace/enterprise/legal-hold`, `/trace/enterprise/retention`, `/trace/enterprise/siem`.
- Dashboard/console-like legacy: `/dashboard`, `/dashboard/citadel`, `/dashboard/operations`, `/dashboard/platform`, `/dashboard/runtime-events`, `/dashboard/status`.
- Other current/legacy pages: `/blog`, `/blog/[slug]`, `/citadel`, `/design-system`, `/enterprise`, `/genesis`, `/products`, `/products/*`, `/register`, `/self-host`, `/self-host/*`, `/treasury`.

### 3.2 Required migration route inventory

| Route | Current owner | Current implementation path | Backend API dependency | Should Reflex own it? | Migration priority | Blocking issues | Safety requirements |
|---|---|---|---|---:|---|---|---|
| `/` | Next.js | `frontend/app/page.tsx`; Reflex partial `reflex_frontend/bastion_ui/routes/home.py` | `/api/v1/public/landing`, `/api/v1/public/status` optional | Yes | P1 | Must preserve public safety/status/fallback copy | Advisory/no-custody/degraded visible |
| `/platform` | Next.js | `frontend/app/platform/page.tsx`; Reflex partial route exists | Public/status/features | Yes | P1 | Match content/nav parity | No custody claims only |
| `/developers` | Next.js | `frontend/app/developers/page.tsx`; Reflex partial route exists | Public docs/OpenAPI links | Yes | P1 | Preserve API envelope docs | Warn no secret material |
| `/operations` | Next.js | `frontend/app/operations/page.tsx`; Reflex partial route exists | Operations/status endpoints optional | Yes | P2 | Must not claim prod readiness | Degraded/runbook visibility |
| `/manifesto` | Next.js | `frontend/app/manifesto/page.tsx`; Reflex partial route exists | None | Yes | P2 | `/self-host` link in manifesto is stale target | No custody/no signing material |
| `/evidence` | Next.js | `frontend/app/evidence/page.tsx`; Reflex partial route exists | Evidence/public stats optional | Yes | P1 | Distinguish public evidence vs Market evidence | Not legal proof |
| `/status` | Next.js | `frontend/app/status/page.tsx`; Reflex partial route exists | `/api/v1/public/status`, trace status optional | Yes | P1 | Must show fallback/stale states | Degraded/stale visible |
| `/roadmap` | Next.js | `frontend/app/roadmap/page.tsx`; Reflex partial route exists | `/api/v1/public/roadmap` optional | Yes | P2 | Avoid contradictory readiness claims | No prod readiness overclaim |
| `/security` | Next.js | `frontend/app/security/page.tsx`; Reflex partial route exists | None | Yes | P1 | Must include sensitive-input warnings | No seed/private key/wallet files |
| `/docs` | Next.js | `frontend/app/docs/page.tsx`; Reflex partial route exists | OpenAPI docs links | Yes | P2 | Keep API path examples accurate | No custody/API limits |
| `/check` | Next.js | `frontend/app/check/page.tsx`; Reflex partial route exists | `/api/v1/trace/lite/{address}`, `/api/v1/public/trace/{report_id}/summary` | Yes | P0 Trace blocker | Reflex must validate public Bitcoin address and reject sensitive material | Required Trace warnings visible |
| `/trace` | Next.js alias to Check page | `frontend/app/trace/page.tsx`; Reflex partial route exists | Same as `/check` | Yes | P0 Trace blocker | Alias must continue to work | Same as `/check` |
| `/trace/[report_id]` | Next.js | `frontend/app/trace/[reportId]/page.tsx`; Reflex partial route exists | `/api/v1/trace/report/{id}`, evidence and panels | Yes | P0 Trace blocker | Bracket param naming differs: Next uses `[reportId]`, target says `[report_id]` | Advisory, limitations, unavailable panel states |
| `/trace/[report_id]/proof-packet` | Next.js | `frontend/app/trace/[reportId]/proof-packet/page.tsx`; Reflex partial route exists | `/api/v1/trace/report/{id}/proof-packet` | Yes | P0 Trace blocker | Must preserve integrity/redaction/advisory fields | Not legal proof; proof packet limitations |
| `/console` | Not in Next.js route tree; Reflex partial route exists | `reflex_frontend/bastion_ui/routes/console.py`; Next has `/dashboard` | Console/status APIs TBD | Yes | P1 | Missing Next route; needs Reflex ownership | Read-only/operator review/no custody |
| `/console/trace` | Not in Next.js route tree; Reflex partial route exists | `reflex_frontend/bastion_ui/routes/console_trace.py` | Trace status/events | Yes | P1 | Must map from legacy dashboard/Trace surfaces | Read-only/advisory |
| `/console/evidence` | Not in Next.js route tree; Reflex partial route exists | `reflex_frontend/bastion_ui/routes/console_evidence.py` | Evidence APIs | Yes | P2 | Missing Next equivalent | Not legal proof |
| `/console/market-intelligence` | Not in Next.js route tree; command palette currently points to `/market` | Reflex partial route exists | Market DTOs/API | Yes, or delegate explicitly | P1 | Ownership split with FastAPI/Jinja `/market` | Stale/fallback visible |
| `/console/time-machine` | Not in Next.js route tree; command palette points to `/market/time-machine` | Reflex partial route exists | `/web/market-time-machine` | Yes, or delegate explicitly | P1 | Must not break Jinja dashboard | Same |
| `/console/sovereign-grid` | Not in Next.js route tree; Reflex partial route exists | `console_sovereign_grid.py` | TBD | Yes | P2 | No Next parity source | Read-only/operator review |
| `/console/policy` | Not in Next.js route tree; Reflex partial route exists | `console_policy.py` | Policy APIs | Yes | P2 | Must avoid auto-approve semantics | Advisory/operator review |
| `/console/audit` | Not in Next.js route tree; Reflex partial route exists | `console_audit.py` | Audit/observability APIs | Yes | P2 | Missing Next equivalent | Evidence-based/no custody |
| `/market` | FastAPI/Jinja | `app/web/routes_market.py`, `templates/market/dashboard.html` | DB via `MarketTimeMachineWebService`; DTO `/web/market-time-machine` | Yes eventually, or delegated during parity | P1 | Currently server-rendered by FastAPI, not Next.js | Market limitations/stale data visible |
| `/market/timeline` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py`, `templates/market/section.html` | DTO/service timeline | Yes eventually | P1 | Current owner is Jinja | Limitations visible |
| `/market/time-machine` | FastAPI/Jinja | `app/web/routes_market.py`, `templates/market/time_machine.html` | `/web/market-time-machine` | Yes eventually | P1 | Current owner is Jinja | Limitations visible |
| `/market/signals` | FastAPI/Jinja via section route | `app/web/routes_market.py` | Service metrics/signals view model | Yes eventually | P2 | Current owner is Jinja | Advisory signals only |
| `/market/evidence` | FastAPI/Jinja via section route | `app/web/routes_market.py` | Service evidence view model | Yes eventually | P2 | Distinguish from public `/evidence` | Not legal proof |
| `/market/narratives` | FastAPI/Jinja via section route | `app/web/routes_market.py` | Service narratives view model | Yes eventually | P2 | Current owner is Jinja | Source limitations |
| `/market/sources` | FastAPI/Jinja via section route | `app/web/routes_market.py` | Source summary | Yes eventually | P2 | Current owner is Jinja | Provider health/staleness |
| `/intelligence/timeline` | FastAPI/Jinja | `app/web/routes_market.py`, `templates/market_timeline.html` | Service timeline | Mirror or redirect after parity | P2 | Legacy/current route must not disappear silently | Limitations visible |
| `/evidence/{packet_id}` | FastAPI/Jinja | `app/web/routes_market.py`, `templates/evidence_viewer.html` | `/web/evidence/{packet_id}` | Mirror or delegate | P2 | Collides conceptually with public `/evidence` | Not legal proof; packet unavailable state |
| `/candles/{candle_id}` | FastAPI/Jinja | `app/web/routes_market.py`, `templates/candle_attribution.html` | `/web/candle/{candle_id}` | Mirror or delegate | P3 | Market-specific detail route | Attribution limitations |

## 4. Current API dependency inventory

### 4.1 Public API

The backend public router is mounted with `settings.api_prefix`, so expected paths are `/api/v1/public/*` when `api_prefix` is `/api/v1`.

| Endpoint | Backend status | Current frontend usage | Notes |
|---|---|---|---|
| `/api/v1/public/landing` | Exists | `frontend/services/apiClient.ts` `getPublicLanding()` | Envelope unwrapped with `body.data`. |
| `/api/v1/public/status` | Exists | `getPublicStatus()`, docs examples | Used by public/status surfaces. |
| `/api/v1/public/roadmap` | Exists | Docs/examples and likely page service | Preserve for Reflex roadmap. |
| `/api/v1/public/stats` | Exists | No direct `apiClient` method found | Add Reflex client if route needs stats. |
| `/api/v1/public/features` | Exists | Developer examples | Add Reflex client if public feature grid needs live data. |
| `/api/v1/public/trace/{report_id}/summary` | Exists | `getTraceSummary(reportId)` | Required by `/check` after lite report lookup. |

### 4.2 Trace API

| Endpoint | Backend status | Current frontend usage | Migration note |
|---|---|---|---|
| `/api/v1/trace/lite/{address}` | Exists | `apiClient.checkTraceLite()` | Required P0 for `/check` and `/trace`. |
| `/api/v1/trace/address/{address}` | Exists | Not used by current Next.js API client | Reflex may need full address workflow or explicitly not use. |
| `/api/v1/trace/report/{report_id}` | Exists | `getTraceReport()` | Required for report page. |
| `/api/v1/trace/report/{report_id}/evidence` | Exists | `getTraceEvidence()` | Required for report evidence panel. |
| `/api/v1/trace/report/{report_id}/proof-packet` | Exists | `getProofPacket()` | Required even though it was not in the initial public API list; it is the proof packet endpoint. |
| `/api/v1/trace/report/{report_id}/privacy-shield` | Exists | `getTracePrivacyShield()` | Required panel. |
| `/api/v1/trace/report/{report_id}/origin-passport` | Exists | `getTraceOriginPassport()` | Required panel. |
| `/api/v1/trace/report/{report_id}/source-summary` | Exists | Not used by current `apiClient` | Add client or document intentional omission. |
| `/api/v1/trace/report/{report_id}/provider-disagreement` | Exists | `getTraceProviderDisagreement()` | Required panel. |
| `/api/v1/trace/report/{report_id}/utxo-hygiene` | Exists | Not used by current `apiClient` | Add Reflex client if UI requires it. |
| `/api/v1/trace/report/{report_id}/dust-radar` | Exists | Not used by current `apiClient` | Add Reflex client if UI requires it. |
| `/api/v1/trace/report/{report_id}/counterparty-lens` | Exists | `getTraceCounterpartyLens()` | Required panel. |
| `/api/v1/trace/report/{report_id}/policy-facts` | Exists | `getTracePolicyFacts()` | Required panel. |
| `/api/v1/trace/status` | Exists | `getTraceStatus()` | Console/status integration. |
| `/api/v1/trace/events` | Exists | `getTraceEvents()`, `getRuntimeEvents()` | Console/runtime events integration. |

### 4.3 Market/API DTOs

| Endpoint | Backend status | Current owner/usage | Migration note |
|---|---|---|---|
| `/web/market-time-machine` | Exists | FastAPI/Jinja DTO endpoint | Reflex Market service should call/mirror this during parity unless replaced by `/api/v1` DTO later. |
| `/web/timeline` | Exists | FastAPI/Jinja DTO endpoint | Required for timeline route parity. |
| `/web/candle/{candle_id}` | Exists | FastAPI/Jinja detail DTO | Required for `/candles/{candle_id}` mirror/delegation. |
| `/web/evidence/{packet_id}` | Exists | FastAPI/Jinja evidence DTO | Required for evidence packet detail mirror/delegation. |
| `/web/market-time-machine/marker-click` | Exists POST | Jinja interaction metric | Reflex should preserve event metrics or document intentional metric change. |
| `/web/market-time-machine/candle-click` | Exists POST | Jinja interaction metric | Same. |
| `/web/market-time-machine/replay-open` | Exists POST | Jinja interaction metric | Same. |
| `/web/market-time-machine/evidence-view` | Exists POST | Jinja interaction metric | Same. |

### 4.4 Frontend/backend mismatches

| Frontend path/code | Missing or mismatched backend endpoint | Recommended fix |
|---|---|---|
| Command palette required final entries say `/console/market-intelligence` and `/console/time-machine`; current Next.js command palette links Market actions to `/market`, `/market/timeline`, `/market/time-machine`, etc. | Not a missing backend endpoint, but a route ownership mismatch. | In Reflex, add required `/console/*` entries and either keep `/market/*` as public Market routes or clearly delegate them to FastAPI/Jinja during parity. |
| Current Next.js has `/dashboard/*`; required final target uses `/console/*`. | No current Next.js `/console` route. | Reflex should own `/console/*`; migration docs should map `/dashboard/*` legacy routes to `/console/*` or archive later. |
| Required Trace contract lists source-summary, utxo-hygiene, dust-radar; Next.js client omits these calls. | Backend endpoints exist. | Add Reflex service methods and UI fallback panels or document not displayed. |
| Required route `/trace/[report_id]`; current Next.js folder is `[reportId]`. | Dynamic naming mismatch only. | Reflex should use bracket syntax `route="/trace/[report_id]"` or documented Reflex-compatible equivalent, while service param can be report_id/reportId internally. |
| `/products/*` and `/self-host/*` still exist as pages while tests assert absent from main nav/palette. | Stale route presence, not backend. | Treat as cleanup blocker for later archive/redirect decision; do not delete before parity. |

## 5. Trace migration blocker analysis

Checklist status:

- [x] Trace backend router exists: `app/api/v1/trace.py`.
- [x] Trace API prefix is known: `app.main` includes `trace_router` with `settings.api_prefix`; expected `/api/v1/trace`.
- [x] `/trace/lite/{address}` exists under `/api/v1/trace/lite/{address}`.
- [x] `/trace/address/{address}` exists under `/api/v1/trace/address/{address}`.
- [x] `/trace/report/{report_id}` exists under `/api/v1/trace/report/{report_id}`.
- [x] `/trace/report/{report_id}/evidence` exists under `/api/v1/trace/report/{report_id}/evidence`.
- [x] `/public/trace/{report_id}/summary` exists under `/api/v1/public/trace/{report_id}/summary`.
- [x] Proof Packet endpoint exists: `/api/v1/trace/report/{report_id}/proof-packet`.
- [x] Trace frontend page exists: `frontend/app/trace/page.tsx` aliases check page.
- [x] `/check` exists: `frontend/app/check/page.tsx`.
- [x] `/trace` alias exists via import from `../check/page`.
- [x] Trace tests exist: `frontend/tests/lite-check.test.tsx`, `frontend/tests/trace-api-contract.test.ts`, `frontend/tests/trace-report-ui.test.tsx`, `frontend/tests/e2e/trace.spec.ts`, plus backend Trace tests under `tests/integration/` and `tests/contract/`.
- [x] Trace is present in navigation: `SiteHeader` includes `/trace`.
- [x] Trace is present in command palette: `Open Trace`, `Check Bitcoin Address`, dynamic report/proof packet actions.

Trace cannot be marked Reflex-ready until all of these pass in Reflex:

- [ ] `/check` works and rejects non-address/sensitive input.
- [ ] `/trace` works as alias or equivalent public Trace landing/check flow.
- [ ] `/trace/[report_id]` works with report, evidence, and panel fallbacks.
- [ ] `/trace/[report_id]/proof-packet` works with unavailable/limitations states.
- [ ] Safety warnings are visible on check, report, and proof packet pages.
- [ ] Forbidden wording is absent from rendered output, excluding test fixtures/constants.
- [ ] Backend API calls match real backend endpoints and unwrap `ResponseEnvelope.data`.
- [ ] Degraded/unavailable/fallback/stale states remain visible rather than hiding panels.

## 6. Market dashboard migration analysis

Checklist status:

- [x] Current `/market` owner: FastAPI/Jinja web dashboard.
- [x] Current `/market` implementation path: `app/web/routes_market.py` with `templates/market/dashboard.html`.
- [x] Current `/market` API/DTO dependencies: `MarketTimeMachineWebService`, `MarketTimelineDTO`, `build_market_dto`, `/web/market-time-machine`.
- [x] Current `/market/time-machine` owner: FastAPI/Jinja.
- [x] Current `/market/timeline` owner: FastAPI/Jinja via `/market/{section}`.
- [x] Current `/market/signals` owner: FastAPI/Jinja via `/market/{section}`.
- [x] Current `/market/evidence` owner: FastAPI/Jinja via `/market/{section}`.
- [x] Current `/market/narratives` owner: FastAPI/Jinja via `/market/{section}`.
- [x] Current `/market/sources` owner: FastAPI/Jinja via `/market/{section}`.
- [x] Current `/web/*` DTO endpoints documented above.
- [x] Reflex should eventually replace public `/market/*` routes only after parity, or explicitly delegate these routes to FastAPI/Jinja for an initial cutover phase.
- [x] Reflex should initially mirror these routes in read-only mode or link/delegate to the Jinja implementation.
- [x] FastAPI/Jinja should remain during the parity phase.

Market migration blockers:

- Market route ownership currently sits outside Next.js and outside the `/api/v1` prefix.
- Reflex needs a `market_client` that supports `/web/market-time-machine`, `/web/timeline`, `/web/candle/{id}`, `/web/evidence/{id}`, plus event metric POSTs or documented metric parity exceptions.
- Market templates include safety limitations through `SAFETY_LIMITATIONS`; Reflex must visibly preserve limitations, data-unavailable states, source health/staleness, and replay/evidence context.
- Current command palette uses `/market/*`; required command palette wants `/console/market-intelligence` and `/console/time-machine`. This must be reconciled without breaking existing `/market/*` routes.

## 7. Navigation and command palette gaps

### Current main navigation

`SiteHeader` current main navigation matches the required final main navigation:

- Platform → `/platform`
- Trace → `/trace`
- Evidence → `/evidence`
- Status → `/status`
- Developers → `/developers`
- Operations → `/operations`
- Docs → `/docs`
- Security → `/security`
- Roadmap → `/roadmap`

`TopNav` also exists and includes older routes (`/citadel`, `/treasury`, `/register`) and should be treated as a secondary/legacy nav component unless still used by pages.

### Current command palette

Current command palette entries include:

- Present and aligned: Open Trace `/trace`, Check Bitcoin Address `/check`, dynamic Open Trace Report `/trace/{reportId}`, dynamic Open Proof Packet `/trace/{reportId}/proof-packet`, Open Evidence `/evidence`, Open Status `/status`, Open Console `/console`.
- Present but path mismatch with required final console entries: Open Market Intelligence currently `/market`, Open Time Machine currently `/market/time-machine`.
- Missing required final entries: `/console/market-intelligence`, `/console/time-machine`, `/console/sovereign-grid`, `/console/policy`, `/console/audit`.
- Additional current entries: Platform, Operations, Developers, Docs, Security, Roadmap, Market Timeline, Market Signals, Market Evidence, Narratives, Sources, Manifesto.
- Stale entries: tests assert `/products` and `/self-host` are not present in the palette, and inspection confirmed the palette does not include them. However, route files and some in-page links still exist for `/products/*` and `/self-host/*`; those remain migration cleanup blockers.

Required Reflex command palette must include exactly or at least:

- Open Trace → `/trace`
- Check Bitcoin Address → `/check`
- Open Trace Report → `/trace/{report_id}`
- Open Proof Packet → `/trace/{report_id}/proof-packet`
- Open Evidence → `/evidence`
- Open Status → `/status`
- Open Console → `/console`
- Open Market Intelligence → `/console/market-intelligence`
- Open Time Machine → `/console/time-machine`
- Open Sovereign Grid → `/console/sovereign-grid`
- Open Policy → `/console/policy`
- Open Audit → `/console/audit`

## 8. Safety copy audit

Required safety copy:

- `Advisory-only.`
- `Not legal verification.`
- `Not Bitcoin consensus proof.`
- `No custody.`
- `Public Bitcoin addresses only.`
- `Never enter seed phrases, private keys, wallet files or signing material.`

Current findings:

| Surface | Compliance | Gaps/blockers |
|---|---|---|
| Next.js `/check` | Strong: warns never enter seed/private/wallet/signing material, public Bitcoin addresses only, advisory, not legal verification or consensus proof. | Copy uses `advisory-only` in some components and `Advisory only` elsewhere; Reflex should standardize required exact copy where tests require exact text. |
| Next.js command palette | Includes advisory-only/no-custody public address workflow text and sensitive report-id rejection. | Needs required console entries and exact final paths. |
| Next.js layout/footer/header | Header nav safe; footer includes advisory/no custody links. | In-page legacy self-host/products links need cleanup decision. |
| FastAPI/Jinja Market | Base footer says no custody; routes inject `SAFETY_LIMITATIONS`. | Must verify every Market template renders limitations in degraded/no-data branches. |
| Reflex scaffold | Contains safety copy constants/helpers and many components/routes with advisory/no-custody warnings. | Must be rendered and tested on every required route before cutover. |

Forbidden wording:

- Required forbidden phrases are `clean-address`, `dirty-address`, `criminal-address`, `guaranteed-safe`, `approved-payment`, `verified-illicit`.
- These phrases appear in Reflex safety/test constants as forbidden-wording lists, which is acceptable in tests/security constants but must not render as claims.
- No production copy migration should introduce those phrases outside explicit “forbidden wording” tests/docs.

## 9. No-custody input audit

Sensitive material explicitly checked for: `seed phrase`, `mnemonic`, `private key`, `xprv`, `yprv`, `zprv`, `wallet.dat`, `keystore`, `12 words`, `24 words`, `signing material`.

| Route/surface | Component/template | Expected input type | Sensitive-material risk | Validation present | Validation missing | Required Reflex validation |
|---|---|---|---|---|---|---|
| `/check`, `/trace` | `AddressCheckForm`, `AddressInput` | Public Bitcoin address | User could paste seed/private key into address field | `validatePublicBitcoinAddress`; safety warnings; disabled submit when invalid | Need full parity in Reflex rendered route tests | Reject sensitive patterns; accept public Bitcoin addresses only; show exact warning. |
| Command palette | `BastionCommandPalette` input | Page search or numeric Trace report id | User could paste mnemonic/private key | `getTraceReportIdFromQuery` rejects seed phrase/mnemonic/private key/xprv/yprv/zprv/wallet.dat/keystore/signing material and only allows numeric report ids | Does not detect “12 words”/“24 words” by phrase count; future test should add phrase-count rejection | Reject sensitive patterns and plausible mnemonic word counts before generating dynamic actions. |
| `/trace/[reportId]` | Dynamic URL param | Numeric/string report id | URL param could contain arbitrary text | API call encodes via service; page route param from URL | Need numeric validation before client calls in Reflex | Only allow expected report-id format; otherwise safe error. |
| `/trace/[reportId]/proof-packet` | Dynamic URL param | Numeric/string report id | Same as above | API call through client | Need numeric validation before client calls in Reflex | Same. |
| Market filters | FastAPI/Jinja query params: timeframe, date, filter, page, page_size, sort, window, status | Filters/sorts/pagination | Low secret risk; user could paste arbitrary text into query params | FastAPI Query constraints for ints and allowlists for timeframes/sections | Sort/filter strings are bounded in metrics but still need UI validation in Reflex | Use allowlists, length limits, encode query params, no secrets. |
| `/evidence/{packet_id}` | Path param | Integer packet id | Low | FastAPI typed `int` | Reflex mirror must type/validate | Numeric-only. |
| `/candles/{candle_id}` | Path param | Integer candle id | Low | FastAPI typed `int` | Reflex mirror must type/validate | Numeric-only. |
| Self-host readiness wizard | `ReadinessWizard` | Deployment profile selections | Low secret risk, but operator config context | Component uses predefined choices/links | Ensure no secret upload/text fields are introduced | No secrets, no seed/private keys, no wallet files. |

## 10. Current tests and missing tests

### Existing Next.js frontend tests

Found under `frontend/tests/`:

- `api-client.test.ts`
- `api-contract.test.ts`
- `business-enterprise-ui.test.tsx`
- `command-palette.test.tsx`
- `foundation.test.tsx`
- `hardening.test.tsx`
- `homepage.test.tsx`
- `lite-check.test.tsx`
- `navigation.test.tsx`
- `pages.test.tsx`
- `platform-dashboard-ui.test.tsx`
- `selfhost-wizard.test.tsx`
- `status-page.test.tsx`
- `trace-api-contract.test.ts`
- `trace-report-ui.test.tsx`
- E2E: `frontend/tests/e2e/home.spec.ts`, `frontend/tests/e2e/trace.spec.ts`

These must be preserved until Reflex parity is proven.

### Existing Reflex tests

Found under `reflex_frontend/bastion_ui/tests/` and `reflex_frontend/tests/`, including route, navigation, API client, safety, no-sensitive-input, console, and scaffold tests. These are promising but do not by themselves prove cutover readiness.

### Required future Reflex tests

- [ ] `tests/test_routes.py`
- [ ] `tests/test_navigation.py`
- [ ] `tests/test_command_palette.py`
- [ ] `tests/test_api_client.py`
- [ ] `tests/test_trace_safety.py`
- [ ] `tests/test_no_sensitive_input.py`
- [ ] `tests/test_forbidden_wording.py`
- [ ] `tests/test_market_routes.py`
- [ ] `tests/test_console_routes.py`

### Verification performed for this audit

- `python -m pytest -q` was run from repository root and failed: 869 passed, 2 skipped, 13 failed. The failures are async tests that are not natively supported in the current pytest environment and require a suitable async plugin such as `pytest-asyncio`; warnings also report unknown `pytest.mark.asyncio`.
- `cd frontend && npm install` completed successfully, with npm audit warnings: 16 vulnerabilities reported by npm (3 moderate, 11 high, 2 critical).
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run test` passed: 9 test files and 26 tests passed.
- `cd frontend && npm run build` passed and generated 63 static/dynamic app routes in the Next.js build output.


## 11. Reflex target architecture

`reflex_frontend/` currently exists. Intended target structure remains:

```text
reflex_frontend/
  rxconfig.py
  pyproject.toml
  uv.lock
  README.md
  Dockerfile
  .env.example

  assets/
    logo.svg
    icons/
    images/
    fonts/
    animations/

  bastion_ui/
    __init__.py
    app.py

    routes/
    components/
    services/
    state/
    theme/
    i18n/
    security/
    tests/
```

Current Reflex scaffold includes most top-level Python/build files and many `bastion_ui/` subpackages. `assets/` was not found in the quick file inventory and should be added later only when needed.

## 12. Reflex route target

Final Reflex route target:

Public:

- `/`
- `/platform`
- `/developers`
- `/operations`
- `/manifesto`
- `/evidence`
- `/status`
- `/roadmap`
- `/security`
- `/docs`
- `/check`
- `/trace`
- `/trace/[report_id]`
- `/trace/[report_id]/proof-packet`

Console:

- `/console`
- `/console/trace`
- `/console/evidence`
- `/console/market-intelligence`
- `/console/time-machine`
- `/console/sovereign-grid`
- `/console/policy`
- `/console/audit`

Market:

- `/market`
- `/market/timeline`
- `/market/time-machine`
- `/market/signals`
- `/market/evidence`
- `/market/narratives`
- `/market/sources`

Dynamic routes should use Reflex bracket syntax, for example:

```python
app.add_page(trace_report_page, route="/trace/[report_id]")
app.add_page(proof_packet_page, route="/trace/[report_id]/proof-packet")
```

## 13. Reflex component target

Required component groups:

- Layout: app shell, public layout, console layout, header, footer, responsive nav, skip link.
- Navigation: main nav, mobile nav, footer nav, command palette, active route handling.
- Safety: advisory banner, no-custody banner, no-sensitive-input warning, degraded/fallback/stale banners, forbidden wording checks.
- Trace: address input, validation notice, check form, loading state, error/unavailable states, Trace Lite result card, report shell, summary card, evidence panel, privacy shield, origin passport, source summary, provider disagreement, UTXO hygiene, dust radar, counterparty lens, policy facts, proof packet viewer.
- Evidence: public evidence dashboard/list/cards, evidence packet detail linkouts, proof packet summary widgets.
- Market: dashboard shell, timeline, time machine chart/table placeholders, signal list, evidence panel, narratives, sources/provider health, candle detail, evidence detail, unavailable/no-data states.
- Console: overview, Trace console, evidence console, Market Intelligence console, Time Machine console, Sovereign Grid, Policy, Audit, read-only/operator-review badges.
- Public pages: platform, developers, operations, manifesto, status, roadmap, security, docs.
- API state components: loading, stale, fallback, empty, degraded, error, retry.

## 14. Migration risks

- **Route ownership risk:** `/market/*` is currently owned by FastAPI/Jinja, not Next.js. A Reflex switch that assumes all public routes are Next.js-owned will break Market routes.
- **Console naming risk:** Current Next.js dashboard routes differ from required `/console/*` routes.
- **API envelope risk:** All Reflex clients must unwrap `ResponseEnvelope.data` and preserve backend error semantics.
- **Sensitive input risk:** Address/report/palette inputs must reject seed phrases, private keys, xprv/yprv/zprv, wallet files, keystores, signing material, and mnemonic-like 12/24 word input.
- **Safety copy drift:** Required exact copy must remain visible; forbidden wording must not appear in rendered UX.
- **Readiness overclaim risk:** Existing docs must not imply Reflex production parity until cutover gates pass.
- **Tooling risk:** Frontend tooling passed after `npm install`, but npm audit reported vulnerabilities; future migration prompts should continue to run real checks and not fake passing tests.
- **Rollback risk:** Next.js and FastAPI/Jinja must remain intact until Reflex has documented parity and deploy rollback.

## 15. Cutover gates

Reflex can become the primary frontend only after all are checked:

- [ ] Reflex builds successfully.
- [ ] Reflex export succeeds.
- [ ] All required public routes exist.
- [ ] All required console routes exist.
- [ ] All required market routes exist or are explicitly delegated.
- [ ] Trace route parity is complete.
- [ ] API client unwraps `ResponseEnvelope.data`.
- [ ] Frontend calls match real backend endpoints.
- [ ] Safety copy is visible.
- [ ] Forbidden wording is absent.
- [ ] No sensitive input is accepted.
- [ ] Degraded/fallback/stale states are visible.
- [ ] Reflex Dockerfile works.
- [ ] docker-compose integration exists.
- [ ] CI workflow exists.
- [ ] Route parity checklist passes.
- [ ] API parity checklist passes.
- [ ] Accessibility baseline passes.
- [ ] Next.js is still available for rollback.

## 16. Recommended prompt sequence 1/22-22/22

1. **Prompt 1/22 — Reflex scaffold reconciliation:** Audit existing `reflex_frontend/`, align structure with target, do not replace routes.
2. **Prompt 2/22 — Reflex routing registry:** Add/verify all public, console, and delegated Market route registrations with route tests.
3. **Prompt 3/22 — Shared safety system:** Centralize exact safety copy, forbidden wording checks, and no-sensitive-input validators.
4. **Prompt 4/22 — API client baseline:** Implement Reflex public/Trace/Market clients with `ResponseEnvelope.data` unwrapping and timeout/error states.
5. **Prompt 5/22 — Navigation parity:** Implement header/footer/mobile nav and command palette with required final entries and stale-entry tests.
6. **Prompt 6/22 — Public page parity:** Migrate public shell pages without changing backend logic.
7. **Prompt 7/22 — Status/Roadmap/Docs parity:** Wire public API clients and fallback/stale states.
8. **Prompt 8/22 — Trace check flow:** Implement `/check` and `/trace` address validation, sensitive-input rejection, and Lite summary flow.
9. **Prompt 9/22 — Trace report flow:** Implement `/trace/[report_id]` report, evidence, panel fallback, and provider-disagreement visibility.
10. **Prompt 10/22 — Proof Packet flow:** Implement `/trace/[report_id]/proof-packet` with integrity/redaction/advisory limitations.
11. **Prompt 11/22 — Evidence public parity:** Implement `/evidence` and proof/evidence public components.
12. **Prompt 12/22 — Console shell:** Implement `/console` and read-only/operator-review posture.
13. **Prompt 13/22 — Console Trace/Evidence:** Implement `/console/trace` and `/console/evidence` clients and UI.
14. **Prompt 14/22 — Console Market/Time Machine:** Implement `/console/market-intelligence` and `/console/time-machine`, delegating to `/web/*` DTOs.
15. **Prompt 15/22 — Console Sovereign Grid/Policy/Audit:** Implement remaining console routes with read-only safe copy.
16. **Prompt 16/22 — Market public mirror:** Mirror or explicitly delegate `/market/*`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`.
17. **Prompt 17/22 — Reflex tests:** Add route, navigation, command palette, API client, Trace safety, no-sensitive-input, forbidden-wording, Market, console tests.
18. **Prompt 18/22 — Build/export/Docker:** Prove Reflex build/export/Dockerfile and document limitations.
19. **Prompt 19/22 — Compose/deploy integration:** Add non-primary docker-compose/deploy integration while preserving Next.js rollback.
20. **Prompt 20/22 — CI parity checks:** Add route/API/safety/accessibility parity checks in CI without production switch.
21. **Prompt 21/22 — Stale route archive plan:** Decide archive/redirect strategy for `/products`, `/self-host`, `/dashboard` only after parity.
22. **Prompt 22/22 — Controlled cutover proposal:** Produce final cutover PR plan, rollback plan, and evidence checklist; do not delete Next.js unless explicitly approved after gates pass.

## 17. Final recommendation

Proceed with Prompt 1/22 by reconciling the already-present `reflex_frontend/` scaffold against this baseline. Do not create a second Reflex app and do not switch production routes. Treat Trace and Market parity as blockers. Keep Next.js and FastAPI/Jinja Market routes intact until every cutover gate is satisfied with passing tests and documented rollback.

## Prompt 1/22 Legacy Freeze Addendum

Prompt 1/22 froze the current Next.js frontend as **legacy-supported** while preserving it for rollback until Reflex parity is complete. No Reflex cutover, route migration, Next.js deletion, Market dashboard deletion, or backend domain rewrite occurred.

Related freeze and inventory documents:

- `frontend/LEGACY_STATUS.md`
- `docs/frontend/FRONTEND_LEGACY_FREEZE.md`
- `docs/frontend/FRONTEND_ROUTE_INVENTORY.md`
- `docs/frontend/FRONTEND_API_DEPENDENCY_INVENTORY.md`
- `docs/frontend/FRONTEND_MIGRATION_BLOCKERS.md`
- `docs/frontend/frontend-route-inventory.json`
- `docs/frontend/frontend-api-dependencies.json`

Prompt 2/22 should use these documents as the route/API inventory source before bootstrapping or reconciling Reflex scaffold work.

## Prompt 2/22 Scaffold Status

- Reflex scaffold created/reconciled in `reflex_frontend/`.
- Current Reflex routes implemented in `bastion_ui/app.py`: `/` only.
- Current status: parallel shell only.
- Next.js status: still legacy active and unchanged by this prompt.
- Market dashboard status: unchanged; FastAPI/Jinja remains owner during parity.
- Trace status: not migrated yet.
- This scaffold does not claim route parity, API parity, production readiness, or Reflex primary frontend status.

## Prompt 3/22 Design System Foundation Status

- Reflex design-system foundation added under `reflex_frontend/bastion_ui/theme/` and `reflex_frontend/bastion_ui/components/`.
- Development preview route added: `/design-system`.
- Current status: reusable UI foundation only.
- Next.js status: still legacy active and unchanged by this prompt.
- Market dashboard status: unchanged; no Market API calls or dashboard migration were added.
- Trace status: not migrated yet; no Trace API calls were added.
- Console status: layout primitives only; no Console business logic was added.
- This prompt does not claim route parity, API parity, production readiness, or Reflex primary frontend status.

## Prompt 4/22 Navigation Parity Status

- Files changed: `reflex_frontend/bastion_ui/navigation.py`, layout navigation components, navigation state modules, command palette state modules, Reflex app preview wiring, README notes, and navigation tests.
- Public nav status: central registry now lists Platform, Trace, Evidence, Status, Developers, Operations, Docs, Security, and Roadmap. Items are marked preview until their Reflex pages are implemented.
- Footer nav status: footer uses the same central public route registry and includes advisory/no-custody safety copy.
- Mobile nav status: mobile metadata includes all public routes, Trace, `/check`, `/console`, and safety copy. Trace is not hidden on mobile.
- Console nav status: sidebar metadata includes Dashboard, Trace, Evidence, Provider Health, Market Intelligence, Time Machine, Sovereign Grid, Policy Engine, Audit Log, Deployment Status, and API Explorer. Incomplete routes are preview or coming-soon shells.
- Command palette status: static actions are registered centrally, and dynamic Trace Report / Proof Packet actions are marked `requires_input=True` without fake report IDs.
- Stale route cleanup status: `/products` and `/self-host` are not canonical Reflex navigation targets; replacements are `/platform` and `/operations`.
- Remaining blockers: business pages remain unmigrated; Trace, Evidence, Market, and Console API workflows still require later prompts; command palette input dialogs and actual route implementations are not complete.

## Prompt 5/22 API Client Layer Status

- Files changed: `reflex_frontend/bastion_ui/config.py`, service client modules, API error models, safe logging utilities, API-layer tests, README notes, and `docs/FRONTEND_API_CLIENT_CONTRACT.md`.
- Config status: `BB_API_BASE_URL`, timeout, feature flags, default language, and log level are environment-backed with safe defaults.
- ResponseEnvelope status: the shared Reflex API client unwraps `data`, raises on non-null `error`, returns raw JSON without `data`, and returns `None` for HTTP 204.
- Error handling status: validation, not-found, rate-limit, unavailable, timeout, connection, and unreadable-response states map to frontend-safe exceptions.
- Client status: public, Trace, Evidence, Status, Market, and Console client foundations exist but do not migrate pages.
- Safe logging status: sensitive wallet/logging material, authorization headers, API keys, webhook secrets, bearer tokens, and mnemonic-like strings are redacted.
- Remaining blockers: Market `/web/*` response shapes require confirmation; provider health, audit summary, and policy summary need stable backend DTO endpoints; no page parity or production cutover is claimed.

## Prompt 6/22 Public Static Routes Migration Status

- Routes implemented in Reflex: `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, and `/docs`.
- Routes intentionally deferred: `/check`, `/trace`, `/trace/[report_id]`, `/trace/[report_id]/proof-packet`, Market dashboard routes, and Console module routes.
- API dependencies used: public static routes document and prepare for `/api/v1/public/landing`, `/api/v1/public/status`, `/api/v1/public/roadmap`, `/api/v1/public/stats`, and `/api/v1/public/features`; pages do not fake live backend data.
- Fallbacks implemented: status page uses a safe unavailable/degraded/stale fallback and roadmap uses conservative labels.
- Safety copy status: Evidence and Security include advisory, no-custody, not-legal-verification, not-consensus-proof, and no wallet-secret input warnings.
- Tests added: public route registration, navigation, safety copy, forbidden wording, fallback status, roadmap labels, and docs completeness labeling.
- Known blockers: Trace public flow, Proof Packet viewer, Market dashboard, Console modules, and production cutover remain deferred until later parity prompts.

## Prompt 7/22 Trace Lite Public Flow Status

- Routes implemented in Reflex: `/check` and `/trace`.
- Backend endpoint used: `/api/v1/trace/lite/{address}` through the shared `BastionApiClient`, with ResponseEnvelope `data` unwrapping preserved.
- Address validation status: accepts plausible public Bitcoin addresses beginning with `bc1`, `1`, or `3`; rejects empty input, obvious non-address text, sensitive wallet material, mnemonic-like phrases, extended private-key prefixes, WIF-looking private keys, wallet files, keystore references, JSON key material, and signing-material wording before API calls.
- Safety copy status: Trace Lite surfaces advisory-only, no-custody, not-legal-verification, not-consensus-proof, and public-address-only copy.
- Result/fallback status: Trace Lite includes empty, loading, safe error, degraded, limitations, and advisory result states without implementing full report pages.
- Routes intentionally deferred: `/trace/[report_id]` and `/trace/[report_id]/proof-packet` remain for Prompts 8 and 9.
- Tests added: Trace route registration, validation, safety copy, API client envelope/error handling, and forbidden wording.

## Prompt 8/22 Trace Report Dynamic Routes Status

- Routes implemented: `/trace/[report_id]` and `/trace/[report_id]/proof-packet` are registered in the Reflex route registry.
- Backend endpoints used: public summary, detailed Trace report, evidence, privacy shield, origin passport, source summary, provider disagreement, UTXO hygiene, dust radar, counterparty lens, policy facts, and proof packet client methods are centralized in `bastion_ui.services.trace_client`.
- Dynamic route safety: report identifiers are validated for empty input, path traversal markers, script-like values, URL schemes, and excessive length before state loading.
- Panel behavior: detailed report panels render explicit unavailable/degraded copy and the state layer treats per-panel failures as partial/degraded data instead of crashing the page.
- Proof packet behavior: the proof packet page shows an unavailable state when backend data is not exposed and does not display placeholder hashes or fabricated packet metadata.
- Safety copy status: Trace report and proof packet views retain advisory-only, no-custody, not-legal-verification, and not-Bitcoin-consensus-proof copy.
- Remaining blockers: live backend schema alignment for each detailed panel, a public-safe proof packet DTO contract, and end-to-end browser validation remain for later prompts.

## Prompt 9/22 — Proof Packet, Evidence, Safety and Limitations UI

- Implemented routes: `/evidence` remains registered as the Evidence overview page and `/trace/[report_id]/proof-packet` remains registered as the route-driven Proof Packet page.
- Implemented components: Evidence card, evidence chain, source badge, confidence badge, limitations card, Proof Packet card, Proof Packet viewer, Proof Packet actions, provider disagreement panel, and degraded evidence banner under `bastion_ui/components/evidence/`.
- Backend endpoints used: `GET /api/v1/trace/report/{report_id}/evidence`, `GET /api/v1/trace/report/{report_id}/provider-disagreement`, `GET /api/v1/trace/report/{report_id}/proof-packet`, and `GET /api/v1/public/trace/{report_id}/summary` through shared API-client handling.
- Backend endpoint mismatches: public-safe Proof Packet DTO availability is still treated as uncertain; the UI shows an unavailable state and does not fabricate packet data when the endpoint is missing, private, or incomplete.
- Safety copy status: Evidence and Proof Packet surfaces show advisory-only, no-custody, not-legal-verification, not-Bitcoin-consensus-proof, public-Bitcoin-data-only, degraded, stale, and provider-disagreement warnings.
- Forbidden wording status: Reflex forbidden-wording tests scan user-facing modules and avoid clean/dirty/criminal/guaranteed/approved/verified-illicit wording.
- Remaining blockers: confirm exact backend Proof Packet DTO, confirm source/fingerprint field naming, and add browser-level loading tests once dynamic route state hydration is finalized.

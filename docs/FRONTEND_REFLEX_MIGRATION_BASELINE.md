# Frontend Reflex Migration Baseline

## 1. Executive summary

This document is the migration baseline for moving Bitcoin Bastion frontend ownership to `reflex_frontend/` under parity gates. It is an audit artifact only: no production route switch, no Next.js removal, no FastAPI/Jinja removal, and no backend domain rewrite occurred.

Key findings:

- `frontend/` is an active Next.js public frontend with public pages, Trace pages, command palette, API clients, and test coverage.
- `app/web/` is an active FastAPI/Jinja Market Intelligence / Market Time Machine dashboard and DTO surface.
- `reflex_frontend/` already exists as a partial scaffold with theme, service, state, security, and tests, but it does not yet own the required route set.
- Trace is migration-critical. Backend Trace endpoints mostly exist, including proof-packet, but frontend route naming uses `[reportId]` while the target Reflex convention should use `[report_id]`.
- The Next.js Trace client references backend endpoints that exist, but also includes status/events/business/enterprise endpoints beyond the minimum target; these should be preserved or explicitly scoped later.
- Market routes are currently owned by FastAPI/Jinja. Reflex should initially mirror/delegate them during parity, not replace them prematurely.
- Stale Next.js pages/actions exist relative to the required final nav, including `/products`, `/self-host`, `/citadel`, `/treasury`, `/register`, `/enterprise`, `/blog`, and `/dashboard/*`.

## 2. Current frontend surfaces

| Surface | Path | Status | Owns routes | Notes |
|---|---|---:|---|---|
| Next.js frontend | `frontend/` | active legacy-to-be | `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`, `/check`, `/trace`, `/trace/[reportId]`, `/trace/[reportId]/proof-packet`, plus many stale/product/dashboard routes | Must remain intact until Reflex reaches documented parity. |
| FastAPI/Jinja web dashboard | `app/web/` | active | `/market`, `/market-time-machine`, `/market/time-machine`, `/market/{section}`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`, `/web/*` DTO/metric endpoints | Current owner of Market Intelligence / Market Time Machine. |
| Reflex frontend | `reflex_frontend/` | partial scaffold | unknown/partial scaffold; target route ownership not complete | Contains `rxconfig.py`, `pyproject.toml`, `Dockerfile`, `bastion_ui/`, services, state, theme, and tests. |

### Required inspection status

| Path | Status |
|---|---|
| `README.md` | exists; documents no-custody posture and Market/Trace status. |
| `docs/STATUS.md` | exists; says Trace frontend routes are baseline implemented. |
| `docs/PRODUCTION_READINESS.md` | exists; says Reflex Trace is not production-primary until parity and deployment evidence are complete. |
| `app/main.py` | exists; mounts API routers and `routes_market`. |
| `app/api/v1/public.py` | exists. |
| `app/api/v1/trace.py` | exists. |
| `app/web/routes_market.py` | exists and is included from `app/main.py`. |
| `frontend/package.json` | exists. |
| `frontend/app/` | exists. |
| `frontend/components/` | exists. |
| `frontend/services/` | exists. |
| `frontend/tests/` | exists. |
| `deploy/` | exists. |
| `Makefile` | exists. |

## 3. Current route inventory

| Route | Current owner | Current implementation path | Backend API dependency | Should Reflex own it? | Priority | Blocking issues | Safety requirements |
|---|---|---|---|---:|---:|---|---|
| `/` | Next.js | `frontend/app/page.tsx` | `/api/v1/public/*` hooks | Yes | P1 | Preserve fallback/stale visibility. | Advisory/no-custody copy visible. |
| `/platform` | Next.js | `frontend/app/platform/page.tsx` | public landing/features indirectly | Yes | P1 | none known | No production-certification wording. |
| `/developers` | Next.js | `frontend/app/developers/page.tsx` plus subroutes | public API docs | Yes | P2 | subroutes need mapping or redirects. | API examples must unwrap `ResponseEnvelope.data`. |
| `/operations` | Next.js | `frontend/app/operations/page.tsx` | public/status or static | Yes | P2 | none known | Degraded states visible. |
| `/manifesto` | Next.js | `frontend/app/manifesto/page.tsx` | static | Yes | P3 | none known | No custody claims. |
| `/evidence` | Next.js | `frontend/app/evidence/page.tsx` | evidence/static dashboard | Yes | P1 | Distinguish public evidence landing from Market evidence packet. | Evidence is advisory, unsigned unless configured. |
| `/status` | Next.js | `frontend/app/status/page.tsx` | `/api/v1/public/status` | Yes | P1 | none known | Must show unknown/degraded/fallback. |
| `/roadmap` | Next.js | `frontend/app/roadmap/page.tsx` | `/api/v1/public/roadmap` | Yes | P2 | none known | Must not claim readiness. |
| `/security` | Next.js | `frontend/app/security/page.tsx` | static/security | Yes | P1 | none known | No seed/private key handling. |
| `/docs` | Next.js | `frontend/app/docs/page.tsx` | static/docs | Yes | P2 | deeper docs route inventory needed. | Public-safe copy. |
| `/check` | Next.js | `frontend/app/check/page.tsx` | `/api/v1/trace/lite/{address}` | Yes | P0 | Must preserve address-only validation. | Never accept seed/private keys/wallet files/signing material. |
| `/trace` | Next.js | `frontend/app/trace/page.tsx` | Trace lite/report client | Yes | P0 | Must remain alias/entry point. | All Trace warnings visible. |
| `/trace/[report_id]` | Next.js equivalent uses `[reportId]` | `frontend/app/trace/[reportId]/page.tsx` | `/api/v1/public/trace/{id}/summary`, `/api/v1/trace/report/{id}`, evidence and panels | Yes | P0 | Dynamic param naming mismatch: target Reflex should use `[report_id]`. | Advisory-only; not legal verification; not consensus proof. |
| `/trace/[report_id]/proof-packet` | Next.js equivalent uses `[reportId]` | `frontend/app/trace/[reportId]/proof-packet/page.tsx` | `/api/v1/trace/report/{id}/proof-packet` | Yes | P0 | Dynamic param naming mismatch. | Must show unsigned/application-level limitations. |
| `/console` | Missing as required route; stale dashboard exists | no `frontend/app/console/page.tsx`; `frontend/app/dashboard/page.tsx` exists | TBD | Yes | P1 | Console route absent; dashboard routes are stale equivalents. | Console safety banner required. |
| `/console/trace` | Missing | none | Trace APIs | Yes | P1 | absent | Same as Trace. |
| `/console/evidence` | Missing | none | evidence APIs | Yes | P2 | absent | Evidence limitations. |
| `/console/market-intelligence` | Missing | none | Market DTOs or delegated Jinja | Yes or delegate initially | P1 | absent; command palette currently points to `/market`. | Degraded/stale data visible. |
| `/console/time-machine` | Missing | none | `/web/market-time-machine` | Yes or delegate initially | P1 | command palette currently points to `/market/time-machine`. | Historical context only. |
| `/console/sovereign-grid` | Missing | none | TBD | Yes | P3 | absent | Avoid unsupported claims. |
| `/console/policy` | Missing | none | policy APIs | Yes | P3 | absent | Advisory policy facts only. |
| `/console/audit` | Missing | none | audit/events APIs | Yes | P3 | absent | No hidden failures. |
| `/market` | FastAPI/Jinja | `app/web/routes_market.py`, templates under `app/web/templates/market/` | DB service + DTOs | Eventually; delegate during parity | P1 | Current owner is Jinja, not Next.js/Reflex. | Limitations and degraded states required. |
| `/market/timeline` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py` | dashboard/timeline service | Eventually; delegate during parity | P1 | Dynamic catch-all maps invalid sections to timeline. | Historical context, not advice. |
| `/market/time-machine` | FastAPI/Jinja | `app/web/routes_market.py` | `/web/market-time-machine` DTO equivalent | Eventually; delegate during parity | P1 | Current duplicate legacy `/market-time-machine`. | Limitations visible. |
| `/market/signals` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py` | dashboard payload | Eventually | P2 | Section is dynamic. | Avoid prediction/causation. |
| `/market/evidence` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py` | dashboard/evidence payload | Eventually | P2 | conflicts conceptually with `/evidence/{packet_id}`. | Evidence limitations. |
| `/market/narratives` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py` | source/narrative payload | Eventually | P2 | Section is dynamic. | Avoid financial advice. |
| `/market/sources` | FastAPI/Jinja via `/market/{section}` | `app/web/routes_market.py` | source summary | Eventually | P2 | Section is dynamic. | Source freshness/degraded visible. |
| `/intelligence/timeline` | FastAPI/Jinja | `app/web/routes_market.py` | timeline service | Maybe redirect/delegate | P2 | Legacy/alternate route. | Same as Market. |
| `/evidence/{packet_id}` | FastAPI/Jinja | `app/web/routes_market.py` | evidence panel/replay | Delegate or reproduce | P1 | Route conflicts with public `/evidence` prefix. | Evidence not proof of legality. |
| `/candles/{candle_id}` | FastAPI/Jinja | `app/web/routes_market.py` | candle attribution | Delegate or reproduce | P2 | Requested route says `/candles/{candle_id}`; DTO is `/web/candle/{candle_id}` singular. | Correlation-not-causation. |

### Actual Next.js routes found

`/blog`, `/blog/[slug]`, `/check`, `/citadel`, `/dashboard`, `/dashboard/citadel`, `/dashboard/operations`, `/dashboard/platform`, `/dashboard/runtime-events`, `/dashboard/status`, `/design-system`, `/developers`, `/developers/api`, `/developers/changelog`, `/developers/contributing`, `/developers/examples`, `/developers/webhooks`, `/docs`, `/enterprise`, `/evidence`, `/genesis`, `/manifesto`, `/operations`, `/`, `/platform`, `/products`, `/products/api`, `/products/bastion-os`, `/products/core`, `/products/crypto-analytics-bot`, `/products/desktop-ai`, `/products/evidence-layer`, `/products/home-ai`, `/products/register`, `/products/sovereign-grid`, `/register`, `/roadmap`, `/security`, `/self-host`, `/self-host/docker`, `/self-host/kubernetes`, `/self-host/production-readiness`, `/self-host/quickstart`, `/self-host/security-checklist`, `/self-host/vps`, `/status`, `/trace`, `/trace/[reportId]`, `/trace/[reportId]/proof-packet`, `/trace/business`, `/trace/business/batch`, `/trace/business/policies`, `/trace/business/review`, `/trace/enterprise`, `/trace/enterprise/audit`, `/trace/enterprise/legal-hold`, `/trace/enterprise/retention`, `/trace/enterprise/siem`, `/treasury`.

Stale or out-of-target routes requiring explicit migration disposition: `/products`, `/self-host`, `/citadel`, `/treasury`, `/register`, `/enterprise`, `/blog`, `/dashboard/*`, `/design-system`, `/genesis`, and business/enterprise Trace subroutes.

## 4. Current API dependency inventory

### Public API

| Endpoint | Backend status | Frontend usage | Notes |
|---|---:|---|---|
| `/api/v1/public/landing` | exists | `frontend/lib/api/public.ts`, `frontend/services/apiClient.ts`, hooks/pages | ResponseEnvelope must be unwrapped. |
| `/api/v1/public/status` | exists | status/home/developers/API client | Fallback state exists. |
| `/api/v1/public/roadmap` | exists | roadmap hook/page | Fallback state exists. |
| `/api/v1/public/stats` | exists | public stats hook | Fallback state exists. |
| `/api/v1/public/features` | exists | features hook | Fallback state exists. |
| `/api/v1/public/trace/{report_id}/summary` | exists | Trace report client | `report_id` is int backend. |

### Trace API

| Endpoint | Backend status | Frontend usage | Mismatch/recommended fix |
|---|---:|---|---|
| `/api/v1/trace/lite/{address}` | exists | `/check`, Trace form/client/tests | Preserve. |
| `/api/v1/trace/address/{address}` | exists | not primary in Next.js client | Keep available; Reflex may use full analysis when needed. |
| `/api/v1/trace/report/{report_id}` | exists | Trace report | Preserve. |
| `/api/v1/trace/report/{report_id}/evidence` | exists | Trace report | Preserve. |
| `/api/v1/trace/report/{report_id}/privacy-shield` | exists | Trace detail panels | Preserve. |
| `/api/v1/trace/report/{report_id}/origin-passport` | exists | Trace detail panels | Preserve. |
| `/api/v1/trace/report/{report_id}/source-summary` | exists | backend only/minor frontend gap | Reflex should add service method if panel requires it. |
| `/api/v1/trace/report/{report_id}/provider-disagreement` | exists | Trace detail panels | Preserve. |
| `/api/v1/trace/report/{report_id}/utxo-hygiene` | exists | not in current main client list | Reflex should include if panel is required. |
| `/api/v1/trace/report/{report_id}/dust-radar` | exists | not in current main client list | Reflex should include if panel is required. |
| `/api/v1/trace/report/{report_id}/counterparty-lens` | exists | Trace detail panels | Preserve. |
| `/api/v1/trace/report/{report_id}/policy-facts` | exists | Trace detail panels/tests | Preserve. |
| `/api/v1/trace/report/{report_id}/proof-packet` | exists | proof packet page | Required though not listed in original minimum Trace API table. |
| `/api/v1/trace/status` | exists | frontend services/tests | Preserve for console. |
| `/api/v1/trace/events` | exists | frontend services/tests | Preserve for console/audit. |

### Market/API DTOs

| Endpoint | Backend status | Current owner | Notes |
|---|---:|---|---|
| `/web/market-time-machine` | exists | FastAPI/Jinja | Primary DTO for dashboard/time-machine. |
| `/web/timeline` | exists | FastAPI/Jinja | Timeline DTO. |
| `/web/candle/{candle_id}` | exists | FastAPI/Jinja | Singular `candle`; HTML route is `/candles/{candle_id}`. |
| `/web/evidence/{packet_id}` | exists | FastAPI/Jinja | Evidence panel DTO. |
| `/web/market-time-machine/marker-click` | exists POST | FastAPI/Jinja | UI metric endpoint. |
| `/web/market-time-machine/candle-click` | exists POST | FastAPI/Jinja | UI metric endpoint. |
| `/web/market-time-machine/replay-open` | exists POST | FastAPI/Jinja | UI metric endpoint. |
| `/web/market-time-machine/evidence-view` | exists POST | FastAPI/Jinja | UI metric endpoint. |

### Frontend/backend mismatches

| Frontend path | Missing/mismatched backend endpoint | Recommended fix |
|---|---|---|
| Next.js route `/trace/[reportId]` | Target route naming says `[report_id]`; backend uses `{report_id}`. | Reflex should use `/trace/[report_id]`; optionally Next.js can remain unchanged until archive. |
| Required `/console/*` routes | No Next.js implementation and no Reflex parity implementation yet. | Add Reflex console routes in later prompts; delegate Market routes initially. |
| Required command palette `/console/market-intelligence`, `/console/time-machine`, etc. | Current palette points Market to `/market` and `/market/time-machine`; lacks sovereign-grid/policy/audit entries. | Update in Reflex and later Next.js cleanup if needed. |
| `/market/timeline` requested | Implemented by dynamic `/market/{section}`, not discrete handler. | Reflex can use explicit route while preserving backend dynamic route. |
| `/candles/{candle_id}` HTML vs `/web/candle/{candle_id}` DTO | Different pluralization. | Document and preserve both roles. |

## 5. Trace migration blocker analysis

Checklist:

- [x] Trace backend router exists: `app/api/v1/trace.py`.
- [x] Trace API prefix is known: `settings.api_prefix` + router prefix `/trace`, normally `/api/v1/trace`.
- [x] `/trace/lite/{address}` exists.
- [x] `/trace/address/{address}` exists.
- [x] `/trace/report/{report_id}` exists.
- [x] `/trace/report/{report_id}/evidence` exists.
- [x] `/public/trace/{report_id}/summary` exists.
- [x] Proof Packet endpoint exists: `/trace/report/{report_id}/proof-packet`.
- [x] Trace frontend page exists: `frontend/app/trace/page.tsx`.
- [x] `/check` exists: `frontend/app/check/page.tsx`.
- [x] `/trace` alias/entry exists.
- [x] Trace tests exist: `frontend/tests/lite-check.test.tsx`, `trace-api-contract.test.ts`, `trace-report-ui.test.tsx`, `e2e/trace.spec.ts`.
- [x] Trace is present in navigation.
- [x] Trace is present in command palette.

Trace is **not ready for Reflex cutover** until Reflex independently proves:

- `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet` route parity.
- visible safety warnings on each Trace entry and result page.
- forbidden wording absent.
- backend calls match real endpoints and unwrap `ResponseEnvelope.data`.
- no sensitive wallet material is accepted.
- proof packet page shows unsigned/application-level limitation where applicable.

## 6. Market dashboard migration analysis

Checklist:

- [x] Current `/market` owner: FastAPI/Jinja in `app/web/routes_market.py`.
- [x] Current `/market` implementation path: `app/web/routes_market.py` + `app/web/templates/market/dashboard.html`.
- [x] Current `/market` API/DTO dependencies: `MarketTimeMachineWebService`, `MarketTimelineDTO`, `/web/market-time-machine`, `/web/timeline`, `/web/candle/{candle_id}`, `/web/evidence/{packet_id}`.
- [x] Current `/market/time-machine` owner: FastAPI/Jinja.
- [x] Current `/market/timeline` owner: FastAPI/Jinja dynamic `/market/{section}`.
- [x] Current `/market/signals` owner: FastAPI/Jinja dynamic `/market/{section}`.
- [x] Current `/market/evidence` owner: FastAPI/Jinja dynamic `/market/{section}`.
- [x] Current `/market/narratives` owner: FastAPI/Jinja dynamic `/market/{section}`.
- [x] Current `/market/sources` owner: FastAPI/Jinja dynamic `/market/{section}`.
- [x] Current `/web/*` DTO endpoints: documented above.
- [x] Reflex should replace these routes eventually after parity.
- [x] Reflex should initially mirror/delegate these routes during parity.
- [x] FastAPI/Jinja should remain during parity phase.

Market blockers:

1. Reflex must model chart, timeline, markers, evidence panel, replay, source summary, limitations, degraded states, and metric POST behavior before route ownership changes.
2. The current backend catches DB `OperationalError` and returns degraded empty states; Reflex must preserve this visibility.
3. Route ownership conflicts exist between public `/evidence` and market packet `/evidence/{packet_id}`.
4. Market DTOs are not ResponseEnvelope-wrapped; Reflex API client must support both raw DTOs and enveloped API responses.

## 7. Navigation and command palette gaps

### Required final main navigation

Required: Platform, Trace, Evidence, Status, Developers, Operations, Docs, Security, Roadmap.

Current `TopNav` includes Platform, Citadel, Trace, Treasury, Register, Developers, Operations, Security, Status, Docs. Missing from required: Evidence, Roadmap. Stale/out-of-target: Citadel, Treasury, Register.

### Required command palette entries

| Entry | Current status |
|---|---:|
| Open Trace → `/trace` | present |
| Check Bitcoin Address → `/check` | present |
| Open Trace Report → `/trace/{report_id}` | present dynamically for numeric query |
| Open Proof Packet → `/trace/{report_id}/proof-packet` | present dynamically for numeric query |
| Open Evidence → `/evidence` | present |
| Open Status → `/status` | present |
| Open Console → `/console` | present, but route absent |
| Open Market Intelligence → `/console/market-intelligence` | missing; current points to `/market` |
| Open Time Machine → `/console/time-machine` | missing; current points to `/market/time-machine` |
| Open Sovereign Grid → `/console/sovereign-grid` | missing |
| Open Policy → `/console/policy` | missing |
| Open Audit → `/console/audit` | missing |

Stale entries explicitly flagged: `/products` exists as pages; `/self-host` exists as pages. They are not in the current command palette, but they are migration cleanup blockers because production navigation/docs may still expose them.

## 8. Safety copy audit

Required safety copy:

- Advisory-only.
- Not legal verification.
- Not Bitcoin consensus proof.
- No custody.
- Public Bitcoin addresses only.
- Never enter seed phrases, private keys, wallet files or signing material.

Current compliance:

- `/check` visibly includes the strongest required no-custody and Trace warnings.
- Trace proof packet backend returns explicit advisory, not legal verification, not consensus proof, no custody, unsigned limitations.
- FastAPI/Jinja Market uses `SAFETY_LIMITATIONS` and degraded/unavailable states.
- README and production readiness docs emphasize no custody and no seed/private-key handling.

Potential failures/gaps:

- Some copy uses variants such as `Advisory only` instead of exact `Advisory-only.`; Reflex should standardize exact strings in shared constants.
- Market pages must continue showing limitations after migration, including provider degraded/unavailable states.
- Console routes are absent, so required console safety copy is absent.

Forbidden wording scan targets:

- clean-address
- dirty-address
- criminal-address
- guaranteed-safe
- approved-payment
- verified-illicit

Existing Next.js tests assert these are absent across key Trace and UI surfaces. Reflex must add equivalent tests and scan route render output.

## 9. No-custody input audit

| Route | Component/template | Input type | Sensitive-material risk | Validation present | Validation missing | Required Reflex validation |
|---|---|---|---:|---|---|---|
| `/check` | `AddressCheckForm` / `AddressInput` | public Bitcoin address | high if user pastes seed/key | client address validation + sensitive phrase checks in tests | backend accepts path string and rejects invalid address; frontend should stay strict | Reject seed phrase, mnemonic, private key, xprv/yprv/zprv, wallet.dat, keystore, 12/24 words, signing material before API call. |
| `/trace` | Trace form components | public Bitcoin address/report workflow | high | Trace components and tests cover sensitive strings | Need Reflex parity | Same as `/check`; public addresses only. |
| command palette | `BastionCommandPalette` text input | route search or numeric report id | medium | rejects URLs, slashes, non-numeric, seed/mnemonic/private key/xprv/wallet.dat/keystore/signing material for dynamic Trace actions | Does not validate general search because it does not submit to backend | Only numeric report IDs may create dynamic Trace links; never echo sensitive material into URLs. |
| `/trace/business/batch` | batch textarea/input | list of public addresses | high | test rejects 12-word mnemonic | Not part of final required routes but must not regress if preserved | Reject all sensitive wallet material and non-public-address values client-side. |
| `/market` | Jinja controls | timeframe/date/selects | low | limited query values/timeframe normalization | date input may be arbitrary date | Normalize timeframe/date; no wallet material field. |
| `/market/time-machine` | Jinja controls | timeframe/date/selects | low | same as above | same as above | Same. |
| `/intelligence/timeline` | Jinja form | filter/window/sort/selects | low | page/page_size bounds in FastAPI | filter string accepts arbitrary labels | Whitelist filters/window/sort in Reflex. |
| `/evidence/{packet_id}` | path param only | integer packet id | low | FastAPI int path param | none | int-only route param. |
| `/candles/{candle_id}` | path param only | integer candle id | low | FastAPI int path param | none | int-only route param. |

Explicit sensitive strings checked for Reflex: `seed phrase`, `mnemonic`, `private key`, `xprv`, `yprv`, `zprv`, `wallet.dat`, `keystore`, `12 words`, `24 words`, `signing material`.

## 10. Current tests and missing tests

### Existing Next.js tests to preserve until Reflex parity

- `frontend/tests/api-client.test.ts`
- `frontend/tests/api-contract.test.ts`
- `frontend/tests/business-enterprise-ui.test.tsx`
- `frontend/tests/command-palette.test.tsx`
- `frontend/tests/e2e/home.spec.ts`
- `frontend/tests/e2e/trace.spec.ts`
- `frontend/tests/foundation.test.tsx`
- `frontend/tests/hardening.test.tsx`
- `frontend/tests/homepage.test.tsx`
- `frontend/tests/lite-check.test.tsx`
- `frontend/tests/navigation.test.tsx`
- `frontend/tests/pages.test.tsx`
- `frontend/tests/platform-dashboard-ui.test.tsx`
- `frontend/tests/selfhost-wizard.test.tsx`
- `frontend/tests/status-page.test.tsx`
- `frontend/tests/trace-api-contract.test.ts`
- `frontend/tests/trace-report-ui.test.tsx`

### Existing Reflex tests found

`reflex_frontend/bastion_ui/tests/` contains scaffold/theme/safety/forbidden-input/forbidden-wording/layout tests. These are a start, not route parity.

### Required future Reflex tests

- `tests/test_routes.py`
- `tests/test_navigation.py`
- `tests/test_command_palette.py`
- `tests/test_api_client.py`
- `tests/test_trace_safety.py`
- `tests/test_no_sensitive_input.py`
- `tests/test_forbidden_wording.py`
- `tests/test_market_routes.py`
- `tests/test_console_routes.py`

Missing coverage blockers:

1. Reflex route existence tests for all public/console/market targets.
2. Reflex API client tests for ResponseEnvelope unwrapping and raw `/web/*` DTO handling.
3. Reflex command palette tests for all required final commands.
4. Reflex no-sensitive-input tests across Trace and command palette.
5. Reflex forbidden wording scan over rendered pages.
6. Reflex market degraded-state tests.
7. Reflex console route tests.

### Verification run status for this audit

- `python -m pytest -q` was attempted during this prompt; see Verification Results below.
- `cd frontend && npm install` was not rerun because `frontend/node_modules` and lock state already exist; running network install is unnecessary for this documentation-only audit.
- `cd frontend && npm run typecheck`, `npm run test`, and `npm run build` were run; see Verification Results below.

## 11. Reflex target architecture

Target structure:

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

Current state: `reflex_frontend/` exists and partially matches this target. Missing or not verified in current scaffold: `assets/logo.svg`, `assets/fonts/`, full route modules, final component set, final service/client set, and final tests listed above.

## 12. Reflex route target

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

Dynamic Reflex registration should use bracket syntax:

```python
app.add_page(trace_report_page, route="/trace/[report_id]")
app.add_page(proof_packet_page, route="/trace/[report_id]/proof-packet")
```

## 13. Reflex component target

Required component groups:

- Layout: `SiteShell`, `PublicLayout`, `ConsoleLayout`, `MarketLayout`, `SiteHeader`, `SiteFooter`, responsive nav.
- Navigation: final main nav, mobile nav, breadcrumbs, command palette.
- Safety: `SafetyBanner`, `SafetyWarning`, `NoCustodyNotice`, degraded/fallback/stale badges.
- Public pages: hero, status strip, roadmap preview, feature grid, docs/developer API blocks.
- Trace: address input, address validation notice, check form, lite result card, report header, summary card, limitations card, evidence summary, privacy/origin/provider/counterparty/policy panels, proof packet viewer, loading/error/unavailable states.
- Evidence: public evidence dashboard/card list, packet summary, export links with unsigned limitations.
- Market: market dashboard, timeframe/date controls, chart shell, marker layer, timeline list, signal panel, narrative panel, source summary, evidence panel, candle attribution panel, replay panel, degraded-state panel.
- Console: console home, Trace console, evidence console, market intelligence console, time-machine console, sovereign grid placeholder, policy console, audit console.
- UI primitives: cards, badges, buttons, forms, table/list, empty state, error state, skeleton, toast/alert.

## 14. Migration risks

1. Premature route cutover could hide Market degraded/fallback states currently handled by Jinja.
2. Trace safety wording regression could create legal/compliance risk.
3. ResponseEnvelope unwrapping mistakes could render envelope metadata instead of data or silently fail.
4. Raw `/web/*` DTOs differ from `/api/v1/*` envelope conventions.
5. Dynamic route naming mismatch `[reportId]` vs `[report_id]` may break links/tests if not standardized.
6. Stale Next.js routes may continue to attract users unless explicitly redirected or archived after parity.
7. Console route absence is a gap in the required target IA.
8. Market route conflicts around `/evidence` vs `/evidence/{packet_id}` need deliberate handling.
9. No-sensitive-input validation must be centralized and tested to avoid accepting seed/private-key material.
10. Reflex scaffold exists, so future prompts must extend it rather than recreate/overwrite it.

## 15. Cutover gates

Reflex cannot become primary frontend until all gates are checked:

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

## 16. Recommended prompt sequence 1/22–22/22

1. Scaffold/normalize Reflex app without route takeover; preserve existing scaffold and add route registry skeleton.
2. Implement shared Reflex theme, layout shell, safety constants, and no-custody notices.
3. Implement Reflex API client with ResponseEnvelope unwrapping, raw DTO support, timeouts, and fallback states.
4. Build public navigation, footer, mobile nav, and command palette parity.
5. Implement public home/platform/status/roadmap/evidence/security/docs/developers pages.
6. Implement `/check` Trace Lite with strict public-address validation and sensitive-input rejection.
7. Implement `/trace` entry page and Trace service methods.
8. Implement `/trace/[report_id]` summary/detail panels against real endpoints.
9. Implement `/trace/[report_id]/proof-packet` with unsigned/application-level limitations.
10. Add Trace safety/forbidden wording/no-sensitive-input tests.
11. Implement console layout and `/console` shell.
12. Implement `/console/trace` and `/console/evidence`.
13. Implement Market DTO client and degraded-state models.
14. Mirror `/market` and `/market/time-machine` in Reflex while keeping Jinja available.
15. Mirror `/market/timeline`, `/market/signals`, `/market/evidence`, `/market/narratives`, `/market/sources`.
16. Implement `/console/market-intelligence` and `/console/time-machine` as Reflex console views.
17. Implement `/console/sovereign-grid`, `/console/policy`, `/console/audit` placeholders with honest limitations.
18. Add route parity and navigation/command palette tests.
19. Add market route/degraded/fallback tests and API contract tests.
20. Add Dockerfile/docker-compose/CI integration checks for Reflex.
21. Run full parity audit; document remaining Next.js/Jinja dependencies and rollback plan.
22. Controlled cutover prompt: only after gates pass, switch primary frontend routing and archive Next.js without deletion.

## 17. Final recommendation

Proceed to Prompt 1/22 by extending the existing `reflex_frontend/` scaffold into a route-registered Reflex baseline. Do not remove or disable `frontend/` or `app/web/`. Treat Trace as the first blocking parity path, and treat Market as a delegated/mirrored surface until Reflex can prove DTO, UI, degraded-state, and safety parity.

## Verification Results

Commands run for this audit should be interpreted as baseline checks, not production readiness evidence.

| Command | Result | Notes |
|---|---:|---|
| `python -m pytest -q` | failed | 864 passed, 18 failed, 2 skipped. Failures are pre-existing/known audit blockers: missing async pytest plugin, partial Reflex scaffold contract gaps, and this baseline initially triggering forbidden wording scan before terms were hyphenated. |
| `cd frontend && npm run typecheck` | passed | Uses existing installed dependencies; npm emitted an `http-proxy` config warning. |
| `cd frontend && npm run test` | passed | 9 test files and 26 tests passed; npm emitted an `http-proxy` config warning and Vite CJS deprecation notice. |
| `cd frontend && npm run build` | passed | Next.js production build completed for 63 app routes; npm emitted an `http-proxy` config warning. |

## Prompt 1/22 Legacy Freeze Addendum

Prompt 1/22 freezes the current Next.js frontend as **legacy but supported until Reflex parity** and records route/API inventories for later migration prompts. The freeze did not delete Next.js, did not migrate routes, and did not attempt Reflex cutover.

Related documents:

- `frontend/LEGACY_STATUS.md`
- `docs/frontend/FRONTEND_LEGACY_FREEZE.md`
- `docs/frontend/FRONTEND_ROUTE_INVENTORY.md`
- `docs/frontend/FRONTEND_API_DEPENDENCY_INVENTORY.md`
- `docs/frontend/FRONTEND_MIGRATION_BLOCKERS.md`
- `docs/frontend/frontend-route-inventory.json`
- `docs/frontend/frontend-api-dependencies.json`

## Prompt 2/22 Scaffold Status

- Reflex scaffold created: `reflex_frontend/` contains `rxconfig.py`, `pyproject.toml`, `README.md`, `.env.example`, `Dockerfile`, and `bastion_ui/`.
- Current routes implemented: `/` only.
- Current status: parallel shell only.
- Next.js status: still legacy active.
- Market dashboard status: unchanged; FastAPI/Jinja remains current owner.
- Trace status: not migrated yet.
- Production status: no route parity, production readiness, or frontend cutover is claimed.

## Prompt 3/22 Design System Status

- Reflex design system foundation created for theme tokens, typography, responsive constants, animations, reusable UI components, layout primitives, feedback states, data stubs, safety notices, and layout/UI state.
- Current Reflex routes implemented: `/` and development-only `/design-system`.
- Current status: reusable foundation only; no business page migration.
- Next.js status: still legacy active.
- Market dashboard status: unchanged; FastAPI/Jinja remains current owner.
- Trace status: not migrated yet.
- Production status: no route parity, production readiness, or frontend cutover is claimed.


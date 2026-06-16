# Frontend Route Inventory

Date: 2026-06-16  
Status labels: `implemented`, `partial`, `missing`, `stale`, `unknown`, `delegated-to-fastapi-jinja`, `blocked`.  
Migration priority labels: `P0 — must migrate before cutover`, `P1 — should migrate before cutover`, `P2 — can migrate after initial Reflex launch`, `Delegated — intentionally owned by non-Reflex surface`.

## Inventory notes

- Current Next.js dynamic route naming uses `[reportId]`; the proposed Reflex route uses `[report_id]`.
- Current Market routes are implemented by FastAPI/Jinja, not by Next.js.
- Current `/console/*` targets are missing from Next.js but partially present in the experimental Reflex tree.
- `/web/*` entries are DTO/action endpoints, not browser pages; they are included because Market and Time Machine parity depends on them.

| Route | Current owner | Implementation path | Current status | Backend dependency | Should Reflex own it? | Migration priority | Blocking issues | Safety notes |
|---|---|---|---|---|---:|---|---|---|
| `/` | Next.js | `frontend/app/page.tsx` | implemented | `/api/v1/public/landing`, `/api/v1/public/status` optional | Yes | P1 — should migrate before cutover | Preserve safety/status copy and fallbacks | Advisory/no-custody/degraded-state copy required |
| `/platform` | Next.js | `frontend/app/platform/page.tsx` | implemented | public status/features optional | Yes | P1 — should migrate before cutover | Content parity needed | Avoid production-readiness overclaims |
| `/developers` | Next.js | `frontend/app/developers/page.tsx` | implemented | public API docs/examples | Yes | P1 — should migrate before cutover | Keep API examples accurate | Warn against secrets/signing material |
| `/operations` | Next.js | `frontend/app/operations/page.tsx` | implemented | operations/status optional | Yes | P2 — can migrate after initial Reflex launch | Must preserve operator/degraded visibility | No custody; self-host claims must be evidence-based |
| `/manifesto` | Next.js | `frontend/app/manifesto/page.tsx` | implemented | none | Yes | P2 — can migrate after initial Reflex launch | Contains legacy `/self-host` link target | No signing/custody claims |
| `/evidence` | Next.js | `frontend/app/evidence/page.tsx` | implemented | evidence/public stats optional | Yes | P1 — should migrate before cutover | Distinguish public evidence from Market evidence packet route | Not legal proof; limitations visible |
| `/status` | Next.js | `frontend/app/status/page.tsx` | implemented | `/api/v1/public/status`, Trace status optional | Yes | P1 — should migrate before cutover | Must preserve fallback/stale states | Degraded/stale visible |
| `/roadmap` | Next.js | `frontend/app/roadmap/page.tsx` | implemented | `/api/v1/public/roadmap` optional | Yes | P2 — can migrate after initial Reflex launch | Avoid contradicting readiness docs | No parity overclaim |
| `/security` | Next.js | `frontend/app/security/page.tsx` | implemented | none | Yes | P1 — should migrate before cutover | Must preserve no-sensitive-input warnings | No seed/private key/wallet-file handling |
| `/docs` | Next.js | `frontend/app/docs/page.tsx` | implemented | OpenAPI/docs links | Yes | P2 — can migrate after initial Reflex launch | Keep API path examples accurate | Advisory/no-custody limits visible |
| `/check` | Next.js | `frontend/app/check/page.tsx` | implemented | `/api/v1/trace/lite/{address}`, `/api/v1/public/trace/{report_id}/summary` | Yes | P0 — must migrate before cutover | Trace blocker; input validation parity required | Public addresses only; no seed/private key/wallet-file input |
| `/trace` | Next.js | `frontend/app/trace/page.tsx` | implemented | same as `/check` | Yes | P0 — must migrate before cutover | Alias must continue to work | Same as `/check` |
| `/trace/[report_id]` | Next.js actual `/trace/[reportId]` | `frontend/app/trace/[reportId]/page.tsx` | implemented | `/api/v1/public/trace/{report_id}/summary`; full report optional | Yes | P0 — must migrate before cutover | Dynamic param naming mismatch; currently summary-focused | Advisory limitations and unavailable states visible |
| `/trace/[report_id]/proof-packet` | Next.js actual `/trace/[reportId]/proof-packet` | `frontend/app/trace/[reportId]/proof-packet/page.tsx` | implemented | `/api/v1/trace/report/{report_id}/proof-packet` | Yes | P0 — must migrate before cutover | Proof Packet route must keep unavailable state | Not legal proof; redaction/integrity limitations visible |
| `/console` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console.py`; legacy Next.js `/dashboard` | partial | console/status APIs TBD | Yes | P1 — should migrate before cutover | Next.js route missing; plan redirects/delegation from `/dashboard` | Read-only/operator-review posture |
| `/console/trace` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_trace.py` | partial | `/api/v1/trace/status`, `/api/v1/trace/events` | Yes | P1 — should migrate before cutover | No Next.js route; route must be verified in Reflex | Advisory/read-only |
| `/console/evidence` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_evidence.py` | partial | evidence APIs TBD | Yes | P2 — can migrate after initial Reflex launch | No Next.js equivalent | Not legal proof |
| `/console/market-intelligence` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_market_intelligence.py` | partial | Market DTO/API endpoints | Yes | P1 — should migrate before cutover | Command palette currently points to `/market` | Stale/fallback states visible |
| `/console/time-machine` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_time_machine.py` | partial | `/web/market-time-machine` | Yes | P1 — should migrate before cutover | Command palette currently points to `/market/time-machine` | Market limitations visible |
| `/console/sovereign-grid` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_sovereign_grid.py` | partial | TBD | Yes | P2 — can migrate after initial Reflex launch | No Next.js equivalent | Read-only/no custody |
| `/console/policy` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_policy.py` | partial | policy APIs | Yes | P2 — can migrate after initial Reflex launch | Must not imply automated approval | Advisory/operator review |
| `/console/audit` | Reflex partial; no Next.js route | `reflex_frontend/bastion_ui/routes/console_audit.py` | partial | audit/observability APIs | Yes | P2 — can migrate after initial Reflex launch | No Next.js equivalent | Evidence-based; degraded visible |
| `/market` | FastAPI/Jinja | `app/web/routes_market.py`; `app/web/templates/market/dashboard.html` | delegated-to-fastapi-jinja | service + `/web/market-time-machine` DTO | Eventually or explicit delegation | P1 — should migrate before cutover | Ownership split; keep Jinja until parity | Market limitations and stale data visible |
| `/market/timeline` | FastAPI/Jinja | `app/web/routes_market.py` via `/market/{section}` | delegated-to-fastapi-jinja | timeline service/DTO | Eventually or explicit delegation | P1 — should migrate before cutover | Section route handles timeline | Limitations visible |
| `/market/time-machine` | FastAPI/Jinja | `app/web/routes_market.py`; `templates/market/time_machine.html` | delegated-to-fastapi-jinja | `/web/market-time-machine` | Eventually or explicit delegation | P1 — should migrate before cutover | Must not break current dashboard | Limitations visible |
| `/market/signals` | FastAPI/Jinja | `app/web/routes_market.py` via `/market/{section}` | delegated-to-fastapi-jinja | service view model | Eventually or explicit delegation | P2 — can migrate after initial Reflex launch | Section route handles signals | Advisory-only signals |
| `/market/evidence` | FastAPI/Jinja | `app/web/routes_market.py` via `/market/{section}` | delegated-to-fastapi-jinja | service view model | Eventually or explicit delegation | P2 — can migrate after initial Reflex launch | Distinct from public `/evidence` | Not legal proof |
| `/market/narratives` | FastAPI/Jinja | `app/web/routes_market.py` via `/market/{section}` | delegated-to-fastapi-jinja | service view model | Eventually or explicit delegation | P2 — can migrate after initial Reflex launch | Section route handles narratives | Source limitations visible |
| `/market/sources` | FastAPI/Jinja | `app/web/routes_market.py` via `/market/{section}` | delegated-to-fastapi-jinja | source summary | Eventually or explicit delegation | P2 — can migrate after initial Reflex launch | Section route handles sources | Provider health/staleness visible |
| `/intelligence/timeline` | FastAPI/Jinja | `app/web/routes_market.py`; `templates/market_timeline.html` | delegated-to-fastapi-jinja | `/web/timeline`; service timeline | Mirror or delegate | Delegated — intentionally owned by non-Reflex surface | Legacy/current route must not disappear silently | Limitations visible |
| `/evidence/{packet_id}` | FastAPI/Jinja | `app/web/routes_market.py`; `templates/evidence_viewer.html` | delegated-to-fastapi-jinja | `/web/evidence/{packet_id}` | Mirror or delegate | Delegated — intentionally owned by non-Reflex surface | Route overlaps conceptually with public `/evidence` | Not legal proof; unavailable state |
| `/candles/{candle_id}` | FastAPI/Jinja | `app/web/routes_market.py`; `templates/candle_attribution.html` | delegated-to-fastapi-jinja | `/web/candle/{candle_id}` | Mirror or delegate | Delegated — intentionally owned by non-Reflex surface | Market detail route | Attribution limitations |
| `/web/market-time-machine` | FastAPI DTO | `app/web/routes_market.py` | implemented | `MarketTimeMachineWebService.dashboard()` | No, Reflex should consume or replace later | Delegated — intentionally owned by non-Reflex surface | Not a page route | DTO must expose limitations/unavailable data |
| `/web/timeline` | FastAPI DTO | `app/web/routes_market.py` | implemented | `MarketTimeMachineWebService.timeline()` | No, Reflex should consume or replace later | Delegated — intentionally owned by non-Reflex surface | Not a page route | DTO must expose limitations |
| `/web/candle/{candle_id}` | FastAPI DTO | `app/web/routes_market.py` | implemented | `MarketTimeMachineWebService.candle_attribution()` | No, Reflex should consume or replace later | Delegated — intentionally owned by non-Reflex surface | Not a page route | Numeric-only id |
| `/web/evidence/{packet_id}` | FastAPI DTO | `app/web/routes_market.py` | implemented | `MarketTimeMachineWebService.evidence_panel()` | No, Reflex should consume or replace later | Delegated — intentionally owned by non-Reflex surface | Not a page route | Not legal proof; numeric-only id |

## Additional current Next.js routes outside target list

These routes exist in `frontend/app/` but are not required target Reflex routes for the initial cutover: `/blog`, `/blog/[slug]`, `/citadel`, `/dashboard`, `/dashboard/*`, `/design-system`, `/enterprise`, `/genesis`, `/products`, `/products/*`, `/register`, `/self-host`, `/self-host/*`, `/trace/business*`, `/trace/enterprise*`, and `/treasury`.

Status: treat as `stale`, `partial`, or legacy-supported until a later archive/redirect prompt decides their fate. Do not delete them in this freeze prompt.

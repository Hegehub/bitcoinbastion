# Reflex Frontend Route Parity

Statuses: `PASS`, `PARTIAL`, `FAIL`, `DELEGATED`, `NOT_APPLICABLE`.

| Route | Legacy owner | Reflex owner | Backend dependency | Parity status | Tests | Blockers | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | Next.js | Reflex | public landing/status | PASS | `test_routes.py`, `test_public_routes.py` | none | Reflex primary |
| `/platform` | Next.js | Reflex | static/public copy | PASS | `test_routes.py`, `test_navigation.py` | none | Reflex primary |
| `/developers` | Next.js | Reflex | docs/static | PASS | `test_routes.py`, `test_navigation.py` | deeper docs remain static | Reflex primary |
| `/operations` | Next.js | Reflex | operations/static | PASS | `test_routes.py`, `test_navigation.py` | none | Reflex primary |
| `/manifesto` | Next.js | Reflex | static | PASS | `test_routes.py` | none | Reflex primary |
| `/evidence` | Next.js | Reflex | evidence/public adapters | PASS | `test_routes.py`, `test_evidence_routes.py` | data may degrade when backend unavailable | Reflex primary |
| `/status` | Next.js | Reflex | `/api/v1/public/status` | PASS | `test_routes.py`, `test_public_api_fallbacks.py` | none | Reflex primary |
| `/roadmap` | Next.js | Reflex | `/api/v1/public/roadmap` | PASS | `test_routes.py` | none | Reflex primary |
| `/security` | Next.js | Reflex | static/security | PASS | `test_routes.py`, safety tests | none | Reflex primary |
| `/docs` | Next.js | Reflex | static/docs | PASS | `test_routes.py` | deeper docs are links/docs | Reflex primary |
| `/check` | Next.js | Reflex | `/api/v1/trace/lite/{address}` | PASS | `test_routes.py`, `test_no_sensitive_input.py`, `test_trace_validation.py` | none | Reflex primary |
| `/trace` | Next.js | Reflex | Trace client | PASS | `test_routes.py`, `test_trace_safety.py` | none | Reflex primary |
| `/trace/[report_id]` | Next.js `[reportId]` | Reflex | `/api/v1/public/trace/{report_id}/summary`, `/api/v1/trace/report/{report_id}` | PASS | `test_routes.py`, `test_trace_report_routes.py` | none | Reflex primary |
| `/trace/[report_id]/proof-packet` | Next.js `[reportId]` | Reflex | `/api/v1/trace/report/{report_id}/proof-packet` | PASS | `test_routes.py`, `test_proof_packet_route.py` | none | Reflex primary |
| `/console` | none/stale dashboard | Reflex | console service adapters | PASS | `test_console_routes.py` | preview/operator-only | Reflex primary |
| `/console/trace` | none | Reflex | `/api/v1/trace/status`, `/api/v1/trace/events` | PASS | `test_console_routes.py`, `test_console_safety.py` | preview/operator-only | Reflex primary |
| `/console/evidence` | none | Reflex | evidence adapters | PASS | `test_console_routes.py` | backend unavailable can degrade | Reflex primary |
| `/console/market-intelligence` | none | Reflex | market adapters | PASS | `test_console_routes.py`, `test_market_intelligence_route.py` | read-only preview | Reflex primary |
| `/console/time-machine` | none | Reflex | time-machine adapters | PASS | `test_console_routes.py`, `test_console_time_machine.py` | read-only preview | Reflex primary |
| `/console/sovereign-grid` | none | Reflex | sovereign-grid adapters | PASS | `test_console_routes.py`, `test_console_sovereign_grid.py` | frontend readiness view | Reflex primary |
| `/console/policy` | none | Reflex | policy review adapters | PASS | `test_console_routes.py` | draft/review only | Reflex primary |
| `/console/audit` | none | Reflex | audit adapters | PASS | `test_console_routes.py` | read-only preview | Reflex primary |
| `/market` | FastAPI/Jinja + Next.js docs | Reflex preview + FastAPI/Jinja active | market/time-machine data | PARTIAL | `test_market_routes.py`, `test_market_safety.py` | FastAPI/Jinja remains active | Delegated/partial |
| `/market/timeline` | FastAPI/Jinja | Reflex preview | market timeline adapters | PARTIAL | `test_market_routes.py` | FastAPI/Jinja detail ownership remains | Delegated/partial |
| `/market/time-machine` | FastAPI/Jinja | Reflex preview | time-machine adapters | PARTIAL | `test_market_routes.py` | FastAPI/Jinja active | Delegated/partial |
| `/market/signals` | FastAPI/Jinja/API | Reflex preview | signal adapters | PARTIAL | `test_market_routes.py` | read-only preview | Delegated/partial |
| `/market/evidence` | FastAPI/Jinja/API | Reflex preview | evidence adapters | PARTIAL | `test_market_routes.py` | detail route delegated | Delegated/partial |
| `/market/narratives` | FastAPI/Jinja/API | Reflex preview | narrative adapters | PARTIAL | `test_market_routes.py` | read-only preview | Delegated/partial |
| `/market/sources` | FastAPI/Jinja/API | Reflex preview | sources adapters | PARTIAL | `test_market_routes.py` | read-only preview | Delegated/partial |
| `/intelligence/timeline` | FastAPI/Jinja | Not Reflex | `app/web/routes_market.py` | DELEGATED | backend/web route coverage | intentionally backend-rendered | Keep delegated |
| `/evidence/{packet_id}` | FastAPI/Jinja | Not Reflex | `app/web/routes_market.py` | DELEGATED | backend/web route coverage | intentionally backend-rendered | Keep delegated |
| `/candles/{candle_id}` | FastAPI/Jinja | Not Reflex | `app/web/routes_market.py` | DELEGATED | backend/web route coverage | intentionally backend-rendered | Keep delegated |

## Decision

Reflex public, Trace, and Console routes pass the controlled-switch gate. Market is partial/delegated, so the switch decision is **SWITCH_PARTIAL_WITH_DELEGATED_ROUTES**.

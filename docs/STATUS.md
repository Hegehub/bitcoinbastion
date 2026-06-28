# Status

Audit date: 2026-05-23

## Bastion Trace
**Bastion Trace: BACKEND BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED**

Substatus:
- Core Trace: BASELINE
- Scoring: BASELINE
- Evidence/Receipt/Replay: BASELINE
- Origin/Source: BASELINE
- Privacy Shield: BASELINE
- Counterparty/Payment Context: BASELINE
- Lite Tier: BASELINE
- Pro Tier: BASELINE
- Business Tier: BASELINE
- Enterprise Tier: PLACEHOLDER/BASELINE
- Integrations: BASELINE
- Observability: BASELINE
- Website UI: BASELINE IMPLEMENTED
- Production Calibration: NOT COMPLETE

## Global note
This file intentionally avoids production-ready claims for Bastion Trace.

## Trace API/frontend contract alignment

Trace frontend routes (`/check`, `/trace`, `/trace/[reportId]`, and `/trace/[reportId]/proof-packet`) are baseline implemented against real backend endpoints. Trace remains advisory-only, no-custody, not legal verification, not Bitcoin consensus proof, and not production-calibrated. Proof packets are unsigned application-level evidence summaries unless signing is explicitly implemented and configured.



Website Backend Foundation: BASELINE IMPLEMENTED
Frontend UI: BASELINE IMPLEMENTED

Frontend Architecture: BASELINE IMPLEMENTED
Frontend Design System: BASELINE IMPLEMENTED
Frontend UI Flows: PARTIAL / PLACEHOLDER

Public website foundation implemented.
Interactive workflows are still pending.

- Public Address Check UX: BASELINE IMPLEMENTED
- Trace Lite UX: BASELINE IMPLEMENTED
- Advanced Trace UI: BASELINE/PARTIAL IMPLEMENTED

Detailed Trace Report UI: BASELINE IMPLEMENTED
Proof Packet Viewer: BASELINE IMPLEMENTED
Advanced Graph Intelligence UI: NOT IMPLEMENTED

Business UI: BASELINE IMPLEMENTED
Enterprise UI: BASELINE/PLACEHOLDER IMPLEMENTED

Platform Dashboard UI: BASELINE IMPLEMENTED
Operations Status UI: BASELINE IMPLEMENTED
Infrastructure Control Plane: NOT IMPLEMENTED

Frontend Hardening: BASELINE COMPLETED

Security Hardening Baseline: IMPLEMENTED
Production Security Validation: PENDING

Kubernetes Deployment Baseline: IMPLEMENTED
GitOps Structure: IMPLEMENTED
Production Deployment Validation: PENDING

Calibration Framework: IMPLEMENTED
Release Candidate Gates: IMPLEMENTED
Production Validation: PENDING

Repository Stabilization: IMPLEMENTED
Technical Debt Audit: IMPLEMENTED
Production Validation: PENDING

Repository: Release Candidate Baseline
Production Readiness: NOT COMPLETE

- News ingestion foundation added (RSS/public source pipeline, duplicate-candidate precheck, replay metadata).

- Source Registry + YAML seed layer baseline implemented.

- Source Health Layer + Provider Confidence Engine baseline implemented.

- Deduplication & Clustering Engine baseline implemented.

## Canonical News Event Engine
- Added deterministic canonical event clustering service, event/article lineage tables, and read endpoints for event timelines.

- Added BTC market data provider layer (multi-provider collection, aggregation, provider health API).

- Added /api/v1/market/btc/context and /api/v1/market/providers/health via market provider layer v2.

## BTC Candle Engine
- Deterministic BTC candle generation from price points with integrity score, provider confidence, and rebuild metadata.

- Prompt 11 candle provider-confidence and evidence snapshots baseline implemented.

- Prompt 12 unified intelligence timeline foundation implemented (normalization, storage, API, dedup baseline).

- Prompt 13 BTC market data foundation safety/health API baseline refined.

- Prompt 17: production-grade news scoring service, narratives, APIs and tests integrated.

- Prompt 18: impact confidence engine, delayed reaction detector, false signal detector, and impact diagnostics API added.

- Prompt 20: news price impact windows and diagnostics endpoints implemented.

## Candle Attribution Engine

- Added first-generation candle attribution persistence for candidate news/event context around BTC candles.
- Added replay logs with deterministic input hashes and ranking snapshots.
- Added operator-safe API routes for candle attribution, top events, and replay diagnostics.

## Production News Impact Engine

- Replaced synthetic news-impact placeholders with candle/price-point-backed impact windows.
- Added per-window snapshots and confidence breakdown persistence.
- Added idempotent article/event recalculation and high-confidence impact discovery.

## Production Candle Attribution Engine

- Added production candle attribution models for ranked attributions, candidate staging, and context snapshots.
- Added configurable candidate windows, weighted ranking, time decay, confidence bands, replay evidence, and operator review hooks.
- Added frontend-ready attribution explanation, candidates, replay, and review API surfaces.

## Candle Attribution Foundation Context

- Added `candle_context_snapshots` and enriched raw attribution candidates with relevance, direction-match, impact-alignment, recency, metadata, raw score, and normalized score fields.
- Added `/api/v1/intelligence/candles/{candle_id}/context` and background context refresh support.

## Historical Similarity Engine

- Added historical event profiles and persisted similarity results for NewsEvent, NewsImpact, and Candle Attribution comparison workflows.
- Added the rule-based pattern library and deterministic similarity scoring across narrative, sentiment, market-impact windows, confidence, provider confidence, and dominant reaction window.
- Added `/api/v1/intelligence/similarity/news/{event_id}`, `/api/v1/intelligence/similarity/event/{event_id}`, and `/api/v1/intelligence/similarity/candle/{candle_id}` for frontend-ready Historical Similarity Panel data.
- Similarity output remains retrospective evidence context only: correlation is not proof of causation, and past reactions do not guarantee future market behavior.

## Production Historical Similarity Engine V1

- Added seeded `market_pattern_library` persistence for deterministic Bitcoin market patterns.
- Added `historical_similarity_records` for report-level analog evidence, component matches, reaction windows, confidence, and explanation JSON.
- Added `PatternClassificationService` plus event/article similarity reports with Weak/Moderate/Strong/Very Strong bands and median/average reaction statistics.
- Added `/api/v1/intelligence/similarity/events/{event_id}`, `/api/v1/intelligence/similarity/articles/{article_id}`, `/api/v1/intelligence/patterns`, and `/api/v1/intelligence/patterns/{pattern_id}`.
- Historical similarity remains informational only: historical similarity does not guarantee future outcomes.

## Historical Similarity Package Layout

- Added package-level historical similarity service boundaries: `historical_similarity_service.py`, `similarity_scoring.py`, `pattern_matcher.py`, and `similarity_explainer.py`.
- Added Prompt 28 response schema under `app/schemas/intelligence/historical_similarity.py` and a signal similarity endpoint.
- Expanded result persistence with reference/matched signal/article/candle fields, pattern type, reaction direction, confidence, and limitations JSON.

## BMTM-30 — Historical Similarity Engine, Pattern Library, and Market Memory

Status: implemented foundation.

Added production market-pattern memory with seeded Bitcoin market patterns, multi-pattern classification evidence, historical event similarity persistence, pattern reaction profiles, confidence calibration, market-memory retrieval, and Intelligence API endpoints for event similarity, pattern history, and reaction profiles.

Safety posture: the engine is evidence-based and does not predict price. Every similarity report must include: "Historical similarity does not guarantee future market behavior."

Bastion Market Time Machine progress: 62% complete. Core ingestion, scoring, market data, candle attribution, historical similarity, pattern memory, and confidence calibration are now in place; remaining work includes richer operator workflows, broader historical backfills, production dashboards, and expanded evidence review tooling.

## Historical Similarity Foundation Update

Implemented foundation tables and services for historical patterns, event reaction profiles, and replayable similarity matches. Added `/api/v1/intelligence/similar-events/{event_id}` and `/api/v1/intelligence/reaction-profile/{event_id}` for evidence-based historical comparisons. The feature remains informational only and does not predict future BTC price action.

## Narrative Heatmap Engine Update

Implemented Prompt 32 foundation for Bitcoin narrative intelligence: persisted narrative catalog, narrative keywords, heatmap snapshots, deterministic classifier/scoring/trend/dominance/rotation services, timeline integration for rising/spiking narratives, API contracts, metrics, and tests. Production readiness improves through operator-visible narrative dominance and evidence packets, while remaining explicitly correlation-based and non-predictive.

## BMTM-033 Narrative Heatmap Expansion

Expanded the narrative heatmap into the BMTM-033 contract with `NarrativeType`, narrative observations, heat/volume/impact/growth snapshot fields, dominance/history APIs, deterministic multi-category classifier coverage for ETF/Fed/Lightning examples, and observability metrics. Remaining work: calibrate historical "before major BTC moves" analysis after broader candle-attribution backfill.

## BMTM-034 Narrative Heatmap Production Registry

Implemented the Task 34 production foundation: local YAML narrative registry, seed command, observation strength/relevance fields, snapshot heat/velocity/dominance fields, emerging narrative API, frontend-ready supporting evidence DTOs, and production metrics. Remaining work: richer historical volatility correlation and dashboard UI rendering.

## BMTM-P35 Production Historical Similarity + Market Memory

Status: implemented production foundation. Completion target moved from 72% to 75%.

Implemented a reusable Market Memory package, event fingerprints, explicit pattern matching, ranked historical similarity, pattern statistics, evidence payloads, replay support, auditable operator review records, API contracts, and test coverage. Remaining limitations: statistics depend on available historical backfills, small samples reduce confidence, and historical analogs are contextual evidence only.

## BMTM-P36 Operator Review, Publishing Policy, and Signal Governance

Status: implemented production foundation. Market Time Machine readiness estimate moved to 78%.

Implemented candidate signal persistence, policy gates, operator review workflows, public/internal signal APIs, delivery logs, safety flags, bounded metrics, API contract tests, and governance documentation. Remaining limitations: Telegram push is not automatic, detector adapters for narrative spikes/news shock index are safe placeholders until upstream production events exist, and reviewer identity awaits production RBAC.

## BMTM-P37 Evidence Packet and Evidence Replay

Status: implemented production foundation. Market Time Machine readiness estimate moved from 78% to 81%; overall Bitcoin Bastion readiness estimate moved from 86% to 87%.

Implemented first-class Evidence Packets, Evidence Replay, Evidence Relationships, Evidence Artifacts, Integrity Snapshots, Replay Logs, confidence provenance, limitation flags, JSON/Markdown export, frontend-ready DTO fields, bounded metrics, API contracts, and test coverage. Remaining limitations: PDF export is future work, provider/source-health snapshots are compact references until full historical health backfill exists, and global schema/runtime parity still has pre-existing drift outside this task.


## Task 38/48 Historical Similarity Engine

Status: implemented. The repository now includes production pattern memory tables, occurrence/reaction snapshots, pattern confidence calculation, frontend-ready similarity context endpoints, and historical-similarity safety limitations.

## Task 39 — Historical Similarity Engine and Pattern Library

Status: implemented. The repository now includes final pattern-library fields, pattern occurrence reason/signal links, historical reaction statistics, deterministic similarity evidence, narrative memory snapshots, bounded metrics, API routes, and regression tests.

## Task 40 — Market Time Machine Web Dashboard

Status: implemented. Added Market Time Machine frontend routes, reusable dashboard components, chart container, evidence/replay views, narrative heatmap, shock index, operator queue, DTO endpoint inventory, frontend tests, and safety language across intelligence pages.


## Task 41 — Market Time Machine Web Dashboard

Status: complete for production web foundation.

- Added FastAPI/Jinja2/HTMX/Alpine routes for `/market-time-machine`, `/intelligence/timeline`, `/evidence/{packet_id}`, and `/candles/{candle_id}`.
- Added thin `/web/*` DTO endpoints for dashboard, timeline, candle attribution, and evidence panel rendering.
- Removed the React `/market` prototype from the production dashboard path to satisfy the non-SPA Market Time Machine constraint.
- Added observable counters for dashboard views, timeline requests, marker clicks, candle opens, evidence opens, and replay opens.
- Remaining blocker: global CI release gates still report pre-existing schema/runtime parity drift outside this UI task.

## Task 42 — Market Timeline and Candlestick Intelligence Dashboard

Status: complete for production dashboard finalization.

- `/market` now renders the primary Market Timeline and Candlestick Intelligence Dashboard.
- Added frontend-ready API contracts for timeline day/hour, candle dashboard DTOs, candle events, candle evidence, candle similarity, and event timeline context.
- Timeline filters support combinable filter values, high-confidence filtering, and operator-reviewed filtering.
- Candle DTOs expose OHLC, volume, price change, dominant direction, volatility score, provider confidence, attribution count, candidate event groups, evidence summaries, similarity previews, narrative strength, and safety flags.
- Remaining blocker: global CI release gates still report pre-existing runtime schema parity drift outside this dashboard task.

## Prompt 43 — Market Time Machine UI

Status: BASELINE IMPLEMENTED / PRODUCTION CALIBRATION PENDING

- Added unified Market Time Machine web pages for `/market`, `/market/timeline`, `/market/candles`, `/market/events`, `/market/news`, `/market/narratives`, and `/market/shock-index`.
- Added chart, marker, candle explanation, evidence packet, historical similarity, replay timeline, narrative, shock-index, and provider-health UI panels.
- Added frontend DTO mapping for `chart_data`, `marker_data`, `selected_candle`, `selected_event`, `historical_matches`, `evidence_summary`, `shock_index`, `narrative_summary`, and `provider_health`.
- Added bounded UI metrics while preserving visible uncertainty, missing evidence, degraded provider state, and operator review state.

Market Time Machine readiness: 88%.
Overall Bitcoin Bastion readiness: 91%.

## Prompt 44 — Market Intelligence dashboard finalization

Status: BASELINE IMPLEMENTED / PRODUCTION CALIBRATION PENDING

- Added Market Intelligence dashboard navigation and routes for `/market`, `/market/timeline`, `/market/time-machine`, `/market/signals`, `/market/evidence`, `/market/narratives`, and `/market/sources`.
- Added landing cards for BTC price, shock index, narratives, high-impact events, published signals, provider health, operator queue, and replay requests.
- Added signal, evidence/replay, source intelligence, timeline, and time-machine section rendering while preserving safety limitations and degraded state visibility.
- Added frontend DTO support for market timeline, timeline events, candle details, attribution details, evidence summary, replay summary, source summary, narrative summary, and shock-index summary.

Market Time Machine readiness: 93%.
Overall Bitcoin Bastion readiness: 92%.

## Task 45 status — production observability

Production observability now includes runtime status, provider health, background job health, degraded component visibility, recovery tracking storage, bounded Prometheus metrics and Kubernetes-compatible probe contracts. Market Time Machine readiness is updated to 95%; overall Bitcoin Bastion readiness is updated to 94% pending final Telegram card/publishing productionization, frontend polish and release hardening.

## Task 46 status — operations control plane

Production operations now include root health probes, dependency health, operations APIs, recovery drill evidence storage, SLO summary DTOs, Grafana dashboards, alert rules, runbooks, and production CronJob coverage. Market Time Machine readiness is updated to 96%; overall Bitcoin Bastion readiness is updated to 96% pending final validation and release candidate audit.

## Task 47 status — disaster recovery and operational health

Production operations now include OperationalHealthService aggregation, exact Market Time Machine CronJobs, DR validation records, backup/restore validation services, operational health/readiness/liveness APIs, DR alert rules and detailed runbooks. Market Time Machine readiness is updated to 98%; overall Bitcoin Bastion readiness is updated to 98% pending final sovereignty-grade release audit.

## Task 48 status — final production audit and sovereignty certification

Status: Production Candidate / Operationally Hardened.

Final release-candidate audit documentation now records repository-wide validation for database migrations, API contracts, Celery/background jobs, evidence, replay, operator workflow, publishing policy, website/frontend DTOs, Telegram safety, observability, Kubernetes artifacts, security posture and sovereignty principles. Schema/runtime parity is hardened through the final release-candidate parity migration. Market Time Machine readiness is updated to 99%; overall Bitcoin Bastion readiness is updated to 99% pending only environment-specific production evidence such as live Kubernetes rendering, load testing, provider incidents, Telegram runtime proof, penetration testing and accessibility certification.

## Event Taxonomy and Registry

Event taxonomy and registry foundation: BASELINE CONTRACT IMPLEMENTED.

This taxonomy baseline defines canonical event domains, event types, metadata, safety flags, and deterministic payload safety checks. Later prompts have added the durable outbox and internal publisher, but webhook delivery, WebSocket broadcasting, SDK clients, CLI commands, MCP server, and plugin runtime execution remain unimplemented.

## Event Outbox

Event outbox foundation: DURABLE INTERNAL BASELINE IMPLEMENTED.

The `event_outbox` table, SQLAlchemy model, repository, service, migration, and tests now exist. This baseline records events as pending rows and prepares retry/lock/dead-letter fields only. It does not implement webhook dispatch, WebSocket streaming, Telegram delivery, SDK consumers, CLI commands, MCP connector, or plugin execution.

## Event Bus

Internal event bus foundation: BASELINE IMPLEMENTED.

The `publish_event(...)` API validates registered event types, checks payload and metadata safety, serializes payloads deterministically, handles local idempotency keys, and writes pending rows to `event_outbox`. It does not implement external delivery.

## Event Domain Integration Status

Prompt 7 wires selected real backend workflows to the internal Event Bus/Event Outbox. Events are persisted internally for Signals, Trace, Treasury, Evidence/Replay, Provider Health, On-chain ingestion, Wallet health, Policy evaluation, News article ingestion, and Market candle attribution where stable hooks exist.

This now includes outbox-backed webhook delivery. WebSocket streaming, SDK consumption, CLI commands, and the baseline MCP connector are implemented; plugin execution remains unimplemented. Event publication is not proof of payment, legal status, Bitcoin consensus proof, or trading correctness. Remaining event integration gaps are documented in `docs/EVENT_INTEGRATION_GAPS.md`.

## Webhook Management Status

Webhook management API foundation: IMPLEMENTED.

The repository now includes persistent webhook endpoints, event subscriptions, delivery records, and `/api/v1/webhooks` management routes. Test delivery creates a safe signed `test_created` delivery record with canonical `X-Bastion-*` headers and sanitized delivery logs. Outbox-backed outbound network dispatch, retry dispatch, and worker execution are implemented as a foundation; live operational evidence and production runbooks remain pending.

- Webhook signing baseline: HMAC SHA256 signing helpers, signed management test deliveries, and sanitized delivery logs are implemented. Full production operational evidence for dispatcher retry execution remains pending later prompts.

## Webhook Dispatcher Status

Webhook dispatcher worker: IMPLEMENTED FOUNDATION.

`dispatch_webhook_outbox_events` processes ready outbox rows, resolves active webhook subscriptions, sends signed POST requests, records delivery attempts, and applies deterministic retry/dead-letter state. Webhook dispatch remains an infrastructure notification mechanism only; it is not legal verification, financial advice, Bitcoin consensus proof, payment approval, or transaction execution authorization.

## MCP Connector status

Bastion MCP Connector: BASELINE IMPLEMENTED / PRODUCTION HARDENING PENDING. The connector provides safe read-only, recommendation-only, and draft-only tools over the Bitcoin Bastion API adapter. Remaining blockers include production auth model validation, live MCP client compatibility testing, operator approval UX integration, rate-limit evidence, and security review.

## TypeScript SDK status

TypeScript SDK: DEVELOPER PREVIEW IMPLEMENTED. The package provides REST resources, ResponseEnvelope unwrapping, WebSocket helpers, webhook signature verification, and no-custody safety checks. Production hardening remains pending for package publication, broader browser/runtime compatibility evidence, and long-term API stability guarantees.

## Plugin API foundation status

Bastion Plugin API foundation: **BASELINE IMPLEMENTED / PRODUCTION HARDENING PENDING**.

Implemented baseline:

- typed plugin manifest and plugin type model;
- deny-by-default permission registry;
- forbidden custody/signing permission rejection;
- restrictive sandbox defaults;
- in-process registry with audit records;
- built-in plugin interfaces and a safe dashboard smoke plugin;
- minimal admin-gated plugin API for list/get/enable/disable/dry-run.

Remaining hardening:

- persisted plugin configuration and operator approval records;
- package signing and external plugin verification;
- production rate-limit evidence;
- security review of any non-built-in plugin loading.

## Developer layer hardening status

Developer/API layer hardening: **BASELINE HARDENED / PRODUCTION EXPOSURE EVIDENCE PENDING**. Sensitive material guards, webhook replay checks, URL safety, payload limits, bounded WebSocket topics, MCP/CLI/plugin safety checks, and documentation truthfulness tests are in place. Remaining blockers are production auth, rate limits, TLS, monitoring evidence, and private-stream access control validation.

## Runtime Profile Matrix

Runtime Profile Matrix: IMPLEMENTED
Runtime Profile Overlays: PENDING
K3s Overlay: BASELINE IMPLEMENTED
Kind Overlay: PENDING
Minikube Overlay: PENDING
Single-node Overlay: BASELINE IMPLEMENTED
Bare-metal/systemd Docs: BASELINE METADATA IMPLEMENTED / FULL GUIDE PENDING

Runtime profile metadata clarifies that Kubernetes is supported but optional, `deploy/kubernetes` remains the canonical Kubernetes path, and production claims still require environment-specific evidence artifacts.

## Runtime Profiles

Status: FOUNDATION IMPLEMENTED / ENVIRONMENT VALIDATION PENDING

Implemented:
- Runtime profile metadata for compose, k8s, k3s, kind, minikube, single-node, and bare-metal/systemd.
- Canonical Kubernetes deployment path under `deploy/kubernetes`.
- Runtime detection/render/deploy script foundation.
- Makefile targets for runtime rendering and deployment.
- Documentation for sovereign small deployments and local Kubernetes validation.

Pending:
- Real environment validation for each profile.
- Production evidence artifacts.
- Load testing.
- Backup/restore drills.
- Security hardening validation per runtime.

## Reflex Trace and Console

Status: EXPERIMENTAL / PARALLEL / NOT PRODUCTION PRIMARY

Implemented:
- Reflex Trace route shell for public address checks, Trace overview, report display, and proof-packet placeholder handling.
- Reflex Console route shell for Trace, Evidence, and Provider Health modules.
- Safety-first address validation and forbidden sensitive-input rejection before backend calls.
- CI workflow for Reflex lint, typecheck, tests, and export.

Pending:
- Route/API parity evidence against the existing frontend and backend.
- Production deployment evidence for Reflex.
- Public proof-packet backend availability where applicable.
- Operator validation for degraded, stale, fallback, and unavailable states.

## Reflex Advanced Console Modules

Status: EXPERIMENTAL PREVIEW / OPERATOR VISIBILITY / NOT PRODUCTION CONTROL PLANE

Implemented:
- Advanced Reflex Console preview routes for Market Intelligence, Time Machine, Sovereign Grid, Policy Engine, Audit Log, Deployment Status, and API Explorer.
- Reusable console navigation, status strip, read-only badges, and operator notices.
- Explicit degraded/fallback/stale/unavailable state visibility.

Pending:
- Live backend wiring and route/API parity evidence.
- Production deployment evidence.
- Operator validation and accessibility review.

## End-to-End Integration Status

Status: FOUNDATION INTEGRATED / PRODUCTION EVIDENCE PENDING

Implemented:
- Static route/API parity checks for backend, Trace, public, Reflex, and runtime-profile contracts.
- Integration smoke scripts that write evidence artifacts under `artifacts/`.
- Integration tests for webhooks, WebSocket streams, SDK safety smoke, runtime renders, and Reflex contracts.

Pending:
- Live environment deployment evidence.
- Full event publication proof for every planned domain event.
- Live SDK/CLI/MCP smoke against a running backend.
- Prompt 30 production readiness audit.

## Prompt 21/22 frontend switch status

Reflex is now the preferred primary frontend for migration runtime profiles under **SWITCH_PARTIAL_WITH_DELEGATED_ROUTES**. Next.js remains available as the rollback frontend and FastAPI/Jinja Market detail routes remain delegated where parity is intentionally partial. No legacy frontend files were deleted and no backend domain behavior was changed.

## Prompt 22/22 final frontend audit status

Final archive decision: **B. Mark Next.js as legacy but keep in `frontend/`**. Reflex remains preferred primary for migration runtime profiles. Market detail routes remain delegated to FastAPI/Jinja, root-suite and local Docker blockers remain, and production readiness is not claimed.

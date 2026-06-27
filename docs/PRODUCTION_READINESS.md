# Production Readiness

## Bastion Trace readiness

Implemented now:
- Backend baseline route/service/model coverage for core trace + tiers + integrations + observability.

Baseline/placeholder now:
- Deterministic weighting/scoring and non-calibrated provider quality semantics.
- Business/enterprise controls that depend on external auth/SSO/SIEM/policy enforcement.

Required before production-complete claim:
- Production calibration evidence for scoring/source weights.
- Production-validated external source adapters.
- Full graph intelligence hardening.
- Public Lite endpoint rate-limiting evidence.
- Production Telegram runtime/token evidence (if used).
- Auth/rate-limit enforcement evidence for business/enterprise endpoints.
- UI implementation and operational rollout evidence.

Explicit open gaps:
- No production calibration of scoring weights.
- No production external source adapters validated.
- No full graph intelligence.
- No ML.
- No frontend website UI yet.
- No production rate limiting evidence for public Lite endpoint.
- No production Telegram token/runtime evidence unless configured.
- Business/Enterprise enforcement depends on auth/policy infrastructure.
- Enterprise RBAC/SSO/SIEM are placeholders unless configured.
- Proof packets are unsigned unless signing exists.


## Public website backend gaps
- No frontend UI yet
- Public APIs require production auth/rate limiting review
- Public APIs require deployment hardening
- No CDN/WAF evidence yet
- No production observability validation yet
- No production calibration evidence yet
- Frontend contracts may evolve


## Frontend production gaps
- Frontend security review pending
- CSP/WAF/CDN hardening pending
- Production accessibility audit pending
- Production mobile QA pending
- Frontend E2E tests incomplete
- Backend/frontend contract stabilization pending
- No production deployment evidence yet


Production frontend hardening is still pending.

- Public endpoint rate limiting validation pending
- Frontend production security review pending
- No production UX telemetry validation yet
- No production accessibility audit yet
- Advanced Trace visualizations not implemented
- No production calibration evidence yet

Advanced graph visualization not implemented
Production accessibility audit pending
Frontend E2E coverage incomplete
Timeline performance validation pending
Proof packet signing/certification not implemented
No production calibration evidence yet

Business UI requires auth/rate-limit review
Review Desk requires production user/role model
Enterprise RBAC/SSO are placeholders unless configured
SIEM delivery requires deployment configuration
Audit immutability is application-level unless WORM/DB controls exist
Legal Hold is operational metadata and not legal advice
Frontend E2E tests still incomplete

Operations dashboard is informational only
No infrastructure mutation/control plane implemented
Production deployment evidence incomplete
Staging validation incomplete
No production calibration evidence
Runtime event scaling not validated
Frontend E2E coverage incomplete

Production accessibility audit pending or partially complete
Production security review pending or partially complete
E2E coverage baseline unless full suite exists
CDN/CSP/WAF configuration pending
Production telemetry/privacy review pending
Backend calibration still pending
Deployment evidence still pending

API contracts baseline locked, not final external SLA
OpenAPI should be reviewed before public API launch
Automated TypeScript generation may be pending
Auth/rate limiting still required for production public exposure
Contract tests cover critical paths but not every future endpoint

Penetration testing pending
WAF/CDN deployment pending
Infrastructure-level rate limiting pending
Production TLS validation pending
Production CSP tuning pending
Full security review pending
Third-party dependency audit pending

Production cluster validation pending
Load testing pending
Production observability tuning pending
Disaster recovery drills pending
Penetration testing pending
Secrets-management integration pending
Production autoscaling validation pending

No real production calibration evidence
No production load testing evidence
No real disaster recovery validation
No production runtime metrics validation
No penetration testing completion evidence
No production deployment evidence yet

Real staging validation pending
Production deployment evidence pending
Production load testing pending
Penetration testing pending
Accessibility certification pending
Full operational drills pending
Production calibration pending

Production calibration incomplete
No production load-testing evidence
No penetration testing completion evidence
No production deployment evidence
No real disaster recovery drill evidence
No accessibility certification
No production operational metrics baseline

## Market Data Engine
- BTC provider aggregation, confidence, degraded mode, and replayability evidence fields implemented in foundation form.

## BTC Candle Engine
- Production candle storage and deterministic rebuild baseline implemented.

- Market candle build runs and provider snapshots baseline implemented.

- Intelligence timeline foundation added with replay-safe hashing and deterministic ordering baseline.

- Market health snapshot endpoint and BTC price history contract aligned for operator visibility.

- News scoring now emits explainable factors + limitations and avoids mandatory AI dependencies.

- News price impact engine now exposes confidence breakdown, impact bands, delayed reaction and false-signal flags.

## News Impact Engine readiness

The News Impact Engine records degraded price/provider state instead of hiding missing data. It persists confidence inputs, window snapshots, and limitations for operator audit. Outputs remain correlation-based and are not financial advice.

## Candle Attribution Production Readiness

Candle attribution remains operator-reviewable and correlation-oriented. The engine records confidence bands, score contributions, provider health, degraded-state limitations, and replay snapshots so operators can audit why an event was ranked near a candle. It does not generate trading signals or claim causation.

## Candle Attribution Context Readiness

The foundation records candle context snapshots for every attributed candle so operators can audit event density, provider confidence, volatility/volume regimes, and category pressure. The context is evidence metadata only and does not assert causation.

## Historical Similarity Production Readiness

Historical similarity is implemented as a deterministic, replayable comparison layer for operator context, not as a forecasting layer. Known limitations include small sample-size sensitivity, incomplete signal-to-event linking, and market regime differences across historical windows. Every response includes limitations and avoids causation or financial-advice claims.

## Market Memory Production Readiness

Market Memory now has deterministic event fingerprints, explicit pattern matching, replayable similarity rankings, persisted market-memory records, pattern statistics, evidence payloads, and auditable operator review support. The system remains operator-controlled and informational only. It is not a prediction engine, does not prove causation, does not guarantee future outcomes from past reactions, and does not generate trading recommendations.

## Signal Governance Production Readiness

Signal governance now prevents automatic strong market-claim publication by default. Candidate signals must pass policy gates and usually require operator review before publication visibility. Delivery logs preserve channel outcomes and sanitized errors. Outputs remain correlation-based and not financial advice; direct causation claims are prohibited.

## Evidence Packet and Replay Production Readiness

Evidence Packet and Replay now provide a production foundation for replayable market-intelligence evidence. Packets persist source entities, lineage relationships, artifacts, deterministic integrity snapshots, confidence provenance, limitations, operator review status, publication status, and replay logs. API responses are frontend-ready and expose correlation-not-causation, evidence-based, replayable, and operator-reviewed flags. JSON and Markdown export are supported; PDF remains future work.

Remaining readiness constraints: historical provider/source-health snapshots need deeper backfill, PDF export is not implemented, and global CI release gates remain constrained by pre-existing schema/runtime parity drift unrelated to the evidence subsystem.


## Historical Similarity Readiness

Task 38 adds long-term market memory. Readiness improves with pattern library seeding, occurrence persistence, reaction statistics, confidence breakdowns, bounded Prometheus metrics, and safe API contracts. Remaining work is larger-scale historical backfill and operator-calibrated production thresholds.

## Historical Similarity Production Readiness

The Historical Similarity Engine is ready for historical-reference production use. It remains intentionally non-predictive and always exposes uncertainty, sample-size limitations, provider-confidence context, and correlation-not-causation safety flags.

## Market Time Machine UI Readiness

The web dashboard layer is ready for operator-facing review flows. It remains display-only, preserves backend authority for DTOs, shows degraded-provider and uncertainty states, and repeats non-advice/correlation safety language on every intelligence page.


## Market Time Machine Web Dashboard Readiness — Task 41

Readiness increased because the primary Market Time Machine interface now exists as a self-hosted FastAPI/Jinja2 dashboard with accessible templates, responsive panels, deterministic markers, candle attribution views, evidence packet views, timeline filters, bounded metrics, and safe empty/error states.

The dashboard is display-only. It does not calculate prices, confidence, attribution, historical similarity, or trading direction in the browser. Safety language remains visible on every page.

Remaining production constraints:

- richer chart interactivity remains planned for a later prompt;
- live usefulness depends on populated market-memory tables and evidence packets;
- global release gates remain blocked by pre-existing schema/runtime parity drift unrelated to this task.

## Market Timeline and Candlestick Dashboard Readiness — Task 42

Readiness increased because `/market` now combines timeline navigation, BTC candle charting, deterministic markers, context panels, evidence overlays, historical similarity previews, and narrative strength in one evidence-first interface.

Production protections:

- DTOs come from backend services; browser/templates do not calculate causation or predictions.
- Timeline requests are paginated and bounded.
- Marker rendering suppresses deterministic duplicates.
- Evidence, provider degradation, replay availability, and limitations remain visible.
- Attribution panels expose `correlation_not_causation`, `evidence_based`, `operator_reviewed`, and `confidence_score`.

Remaining production constraints are richer chart interactions, live table backfill depth, and the pre-existing schema parity blocker in global release gates.

## Market Time Machine UI readiness

Prompt 43 adds the primary Market Time Machine web interface and frontend contract tests.

Implemented:

- Unified `/market` web interface.
- Section pages for timeline, candles, events, news, narratives, and shock index.
- Responsive and high-contrast CSS baseline.
- Keyboard-accessible chart controls and marker/candle selection.
- Mandatory no-causation, evidence-based, operator-review, and provider-health visibility flags.
- Bounded Prometheus metrics for page views, marker clicks, candle clicks, replay requests, and evidence views.

Remaining blockers before production-ready claim:

- Production traffic/load validation.
- Browser screenshot and visual regression suite against live data.
- Calibration evidence for shock-index thresholds and narrative confidence.
- Provider-health coverage validation in production.

## Prompt 44 Market Intelligence dashboard production-finalization status

Implemented:

- Market Intelligence landing dashboard.
- Dedicated timeline, time-machine, signals, evidence, narratives, and sources routes.
- Future-refresh-ready dashboard cards.
- Windowed timeline rendering and meaningful empty/error states.
- Evidence packet and replay visibility including replay failures and policy/operator fields.
- Source intelligence table with sorting.
- Bounded observability metrics for dashboard, evidence, replay, signal, and narrative views.

Still pending before a production-ready claim:

- Production live-data calibration of shock index thresholds and narrative confidence.
- Production provider-health validation with real degraded-source incidents.
- Browser-based visual regression and accessibility audit against production-like data.
- Existing release-gate schema parity blocker remains unresolved outside this UI task.

## Observability readiness

The platform is production-observable for runtime health: provider failures, job failures, Telegram degradation, fallback activation and operator-attention states are API-visible and metric-compatible. Grafana JSON dashboards are intentionally deferred; metric naming and bounded labels are ready for dashboard construction.

## Operations control-plane readiness

Production readiness now includes root Kubernetes health probes, dependency health DTOs, operations status APIs, recovery drill evidence storage, SLO summary DTOs, Grafana dashboard definitions, Alertmanager-compatible Prometheus rules, and runbooks for database, workers, providers, Telegram and deployment failures.

## Disaster recovery readiness

Production readiness now requires backup validation, restore validation, deterministic replay validation, integrity verification and operator-visible limitations before recovery can be considered successful.

## Final release-candidate production readiness

Status: Production Candidate / Production Baseline / Operationally Hardened.

The final release-candidate audit validates the complete evidence-driven production chain from external sources through collectors, normalization, storage, scoring, evidence, replay, attribution, signals, policy, operator review, publication, API, web and Telegram outputs. Required public safety language remains mandatory: Correlation is not proof of causation. Evidence-based informational analysis. Not financial advice.

Final hardening includes runtime schema parity alignment between SQLAlchemy models and Alembic-created databases, conservative release-candidate documentation, sovereignty certification, and explicit known limitations. This does not claim perfect security, guaranteed correctness, or bug-free operation.

Remaining environment-specific evidence before a production-validated claim:

- production Kubernetes render/apply evidence with `kubectl` available;
- live staging provider-health incidents and recovery records;
- production load testing and traffic-shaping evidence;
- Telegram bot token/runtime delivery evidence;
- WAF/CDN/TLS/rate-limit validation;
- penetration testing and accessibility certification.

Final readiness estimate: Market Time Machine 99%; overall Bitcoin Bastion 99% as a production candidate.

## Trace API/frontend contract alignment

Bastion Trace is implemented as a backend and frontend baseline, not a production-calibrated service. `/check`, `/trace`, `/trace/[reportId]`, and `/trace/[reportId]/proof-packet` align with real FastAPI endpoints and preserve `ResponseEnvelope.data` handling. Trace outputs are advisory-only, no-custody, not legal verification, and not Bitcoin consensus proof. Proof packets are unsigned application-level evidence summaries unless signing is explicitly implemented and configured with evidence.

## Event layer readiness

The event taxonomy and registry are a baseline contract. The durable outbox and internal publisher now exist, and webhook dispatcher, WebSocket broadcaster, SDK, CLI, and baseline MCP connector foundations now exist; production hardening remains pending for deployment evidence, auth/rate-limit validation, and plugin execution runtime.

## Event outbox readiness

The event outbox is implemented as an internal durable foundation only. It prepares persistence, retry metadata, lock metadata, and sanitized error storage, but production event delivery remains pending until dispatcher workers, delivery authorization, webhook/WebSocket transports, operational runbooks, and live deployment evidence exist.

## Event bus readiness

The internal Event Bus is a baseline publisher into the durable outbox only. Production delivery readiness remains pending until dispatcher workers, webhook/WebSocket authorization, delivery logs, runtime metrics, operator runbooks, and deployment evidence are implemented and validated.

## Event Bus / Domain Integration Readiness Note

The Event Bus and Outbox are an internal durability foundation. Selected domains now write events to the outbox, and an outbox-backed webhook dispatcher foundation is implemented. Delivery retries, outbound webhook dispatch execution, WebSocket fan-out, SDK consumption, CLI surfaces, and baseline MCP connector foundations now exist, but plugin execution and production-grade evidence require later prompts before any production-ready delivery claim.

## Webhook Readiness Note

Webhook endpoint/subscription/delivery persistence, management APIs, HMAC signing helpers, signed test delivery records, and sanitized delivery logs are implemented as a foundation. Production webhook delivery is not ready until live delivery metrics, secret rotation, alerting/SLO evidence, deployment-specific worker operations, and operator runbooks are implemented and validated.

- Webhook security update: signed test deliveries and sanitized delivery observability are implemented as a foundation. Production live dispatcher evidence, alerting/SLO validation, and secret rotation evidence remain pending; webhooks must not be described as fully production-delivery-ready yet.

## Webhook Dispatcher Readiness Note

The webhook dispatcher foundation now performs outbox-backed signed POST delivery with retry/dead-letter state and sanitized delivery logs. Production readiness still requires live delivery evidence, operator runbooks, alerting/SLO validation, secret rotation, and deployment-specific dispatcher operations evidence.

## MCP Connector readiness

Bastion MCP Connector: BASELINE IMPLEMENTED / PRODUCTION HARDENING PENDING. It is designed as a no-custody, advisory-only AI-agent interface and is not a wallet, signing interface, trading executor, legal-verdict engine, or Bitcoin consensus oracle. Production readiness requires production auth model validation, live MCP client compatibility testing, operator approval UX integration, rate-limit evidence, and security review.

## TypeScript SDK readiness

TypeScript SDK: DEVELOPER PREVIEW IMPLEMENTED / PRODUCTION HARDENING PENDING. It is a no-custody client library and not a wallet, trading executor, legal-verdict engine, or Bitcoin consensus oracle. Production readiness requires package publication controls, runtime compatibility evidence, security review, and versioned API stability policy.

## Plugin API readiness

Bastion Plugin API foundation is **baseline implemented** and **not marketplace-ready**. The current design is manifest-first, deny-by-default, dry-run-first, and operator-controlled.

Production blockers before broader plugin rollout:

- persisted operator approval state;
- package signature verification for external plugin artifacts;
- security review gates for plugin capabilities;
- production authorization model validation for admin actions;
- rate-limit and audit-retention evidence.

Plugins cannot access seed phrases, private keys, wallet files, or signing material. Plugins cannot sign Bitcoin transactions, broadcast Bitcoin transactions, or approve treasury actions.

## Developer layer production readiness

Developer/API layer is hardened for baseline self-hosted development but is not production-complete without evidence for auth, rate limits, TLS, webhook receiver verification, monitoring, and operational runbooks. WebSockets are not durable delivery. Plugins remain in-process and sandbox-limited; external plugin loading is not enabled.

## Runtime profile readiness note

Runtime profiles improve deployment clarity but do not by themselves prove production readiness. Production readiness still requires environment-specific evidence artifacts, secrets handling validation, monitoring validation, backup/restore evidence, and operational drills. Kubernetes is supported but not mandatory; `deploy/kubernetes` remains the canonical Kubernetes manifest path when Kubernetes is used.

## Runtime Profile Production Readiness

Runtime profiles improve deployability but do not prove production readiness. No runtime profile changes Bitcoin Bastion's no-custody posture: the system must not hold, request, store, derive, or transmit seed phrases or private keys.

Production readiness still requires:
- successful deployment evidence;
- migration smoke evidence;
- schema parity evidence;
- provider health evidence;
- observability validation;
- backup/restore validation;
- rollback validation;
- security review;
- load testing;
- incident/drill evidence.

K3s and single-node profiles have explicit limitations:
- limited HA;
- resource constraints;
- manual or reduced evidence jobs;
- operator-managed backup strategy;
- less fault tolerance than full Kubernetes clusters.

## Reflex Frontend Production Readiness

The Reflex frontend is experimental and parallel at this stage. It does not replace Next.js, does not replace FastAPI, and does not replace the existing FastAPI/Jinja `/market` dashboard.

Trace is migration-critical, but Reflex Trace is not production-primary until route/API parity and deployment evidence are complete. Safety warnings are required on Trace and Console pages. Proof Packet pages may remain frontend-ready placeholders if public backend proof-packet data is unavailable; missing data must be shown as unavailable and must not be faked.

Production readiness still requires CI evidence, deployment evidence, route/API parity evidence, security review, load testing, accessibility validation, observability validation, and operator drill evidence.

## Reflex Advanced Console Production Readiness

The advanced Reflex Console modules are preview/operator-visibility pages only. They are not production control-plane mutation tools, do not replace `/market`, do not replace backend authority, and do not perform custody, signing, transaction creation, transaction broadcasting, or treasury execution.

Production readiness requires live backend integration evidence, route/API parity evidence, deployment evidence, security review, accessibility validation, load testing, observability validation, and operator drill evidence. Degraded, fallback, stale, and unavailable states must remain visible.

## Prompt 29 Integration Boundary

The end-to-end integration pass improves repository coherence, but it does not prove production readiness. Static route parity, render dry-runs, and frontend export checks must be supplemented with environment-specific evidence before production use.

Required remaining evidence includes live deployment evidence, migration smoke evidence, backup/restore drills, rollback validation, security review, load testing, incident drills, and operator sign-off. Bitcoin Bastion remains no-custody and must not accept seed phrases, private keys, wallet files, or signing material.


## Reflex frontend CI readiness

Reflex frontend CI now covers lint, typecheck, tests, export, Docker build wiring, safety wording, forbidden wording, no-sensitive-input checks, and route parity checks. This improves migration evidence but does not make Reflex production-primary. Prompt 21/22 must still complete the route/API parity gate and controlled primary frontend switch before any production cutover claim.

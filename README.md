# Bitcoin Bastion

> **Bitcoin-first sovereign backend for evidence-driven market intelligence, operational resilience, and production-grade self-hosted deployment.**

[Website](https://bitcoin-bastion.com) • [Documentation](docs/INDEX.md) • [Current Status](docs/STATUS.md) • [License](LICENSE)

![Status](https://img.shields.io/badge/status-development%20baseline%20--%20gates%20failing-red)
![Bitcoin First](https://img.shields.io/badge/bitcoin-first-f7931a)
![No Custody](https://img.shields.io/badge/no--custody-enforced-brightgreen)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Kubernetes](https://img.shields.io/badge/kubernetes-supported-326ce5)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

**Bitcoin Bastion** is a Bitcoin-first backend platform designed to provide operators, builders, analysts, and Bitcoin‑native systems with transparent, auditable and evidence‑driven market intelligence, provider health, operational readiness and deployment verification. It is *not* a wallet, custodian, automated trading bot, or consensus replacement.  Instead it acts as a sovereignty‑grade backend foundation for:

- Bitcoin market and news intelligence;
- provider‑health monitoring and confidence tracking;
- explainable runtime status and observability;
- risk and evidence analysis (Citadel layer);
- operational recovery checks and evidence collection;
- deployment and release evidence with Kubernetes‑based production control.

The platform aims to make Bitcoin infrastructure more transparent, auditable, reproducible, self‑hostable and evidence‑driven while preserving a strict no‑custody posture.

## Core documentation

Start with the [documentation index](docs/INDEX.md). It identifies the current
canonical documents for architecture, API contracts, Access and wallet
security, Market intelligence, Trace, frontend, storage, operations, deployment,
and release governance. Revision-bound audits and superseded migration reports
are retained under `docs/archive/` and are not current guidance.

## Design philosophy

Bitcoin Bastion follows a strict set of design principles:

| Principle                     | Meaning                                                                                                  |
|------------------------------|------------------------------------------------------------------------------------------------------------|
| **Bitcoin‑first**            | Bitcoin is the primary design reference. Other assets, if ever supported, must remain isolated and optional. |
| **No custody**               | The system must not hold, request, store, derive, or transmit seed phrases or private keys.                  |
| **Operator control**         | Risky actions require explicit operator awareness and approval.                                              |
| **Evidence over claims**     | Runtime state, deployment readiness and provider quality must be backed by artifacts.                        |
| **Self-hosted capable**      | The system should be deployable on VPS, bare metal, homelab or private Kubernetes clusters.                  |
| **No black‑box trust**       | External providers are fallible and must be observable.                                                      |
| **Explicit limitations**     | Synthetic, degraded, fallback and baseline states must remain visible.                                       |
| **Rollback discipline**      | Production deployment must have a documented rollback path.                                                  |
| **Auditability**             | Release decisions should be explainable and supported by evidence.                                           |


## Authentication: Bastion Proof-of-Access

Bitcoin Bastion no longer uses password login for protected access. Protected access is based on payment proof, an issuer-signed access right, subscription entitlement, device possession, short-lived Proof-of-Possession sessions, request signatures, revocation checks, and Policy Engine decisions.

A Bastion Access Pass is not a bearer token and must not be sent as `Authorization: Bearer`. The project is non-custodial: Bastion never asks for Bitcoin seed phrases, Bitcoin private keys, xprv material, or wallet files.

Start with [`docs/ACCESS_LAYER.md`](docs/ACCESS_LAYER.md), [`docs/API_ACCESS.md`](docs/API_ACCESS.md), [`docs/ACCESS_REQUEST_SIGNING.md`](docs/ACCESS_REQUEST_SIGNING.md), [`docs/ACCESS_RECOVERY.md`](docs/ACCESS_RECOVERY.md), and [`docs/ACCESS_ENVIRONMENT.md`](docs/ACCESS_ENVIRONMENT.md).

## Current status (15 July 2026)

The repository is a substantial development baseline with implemented
subsystems, but it is **not currently release-candidate or production-ready**.
Focused Proof-of-Access and Wallet/LNURL tests pass, while the merged `main`
revision still has failing CI, integration, code-quality, and schema-parity
gates. The documentation-truthfulness remediation passes in the current working
tree but is not part of a new immutable revision yet. Wallet/LNURL is foundation-only until its
runtime/API wiring is completed. See [STATUS.md](docs/STATUS.md) for the verified
snapshot and [PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) for the
evidence required to promote a specific revision and environment.

## Main components

The platform consists of multiple layers:

- **FastAPI backend** – exposes application APIs, health/readiness and admin endpoints, coordinates core services and collects release evidence.
- **Core services** – provider health, market/news intelligence, delivery logic, recovery checks, protocol advisory and Citadel evidence layer.
- **Data layer** – PostgreSQL with SQLAlchemy and Alembic migrations; supports migration smoke tests and schema parity validation.
- **Background runtime** – Celery workers and beat, Redis broker/cache and scheduled jobs for health collection, recovery checks and evidence tasks.
- **Evidence layer** – release evidence, migration smoke evidence, schema parity evidence, provider evidence, observability snapshot and deployment evidence pack.
- **Kubernetes runtime layer** – manifests for API/worker/beat deployments, migration/evidence jobs, CronJobs for provider health and recovery drills, NetworkPolicy, ServiceMonitor, GitOps templates and production runbooks.
- **Market Time Machine** – web dashboard `/market` providing timeline navigation, BTC candles, deterministically scored news markers, candle context, attribution confidence, historical similarity previews, narrative heatmap and shock index.
- **Event & plugin layer** – internal event taxonomy, outbox, bus and webhook management for safe notifications; plugin API foundation for deterministic extension points with restrictive sandbox defaults and audit records.

## Services directory

The `app/services` package contains the core domain services that implement the platform’s business logic.  Each service encapsulates a cohesive set of responsibilities and publishes domain events through the event bus.  At a high level:

### Bastion Trace

`bastion_trace` evaluates the risk associated with a Bitcoin transaction or UTXO.  `TraceService` coordinates a series of heuristics—including dust‑radar, false‑positive guards, UTXO hygiene checks, privacy shield lookups and payment‑context risk evaluations—to compute a **trace band** (low, medium, high).  It assembles a `TraceReport`, stores it, and publishes a `trace.report.created` event to the event bus for asynchronous consumers.  A companion `LiteTraceReportService` maps trace bands to human‑readable labels and suggested operator actions.

### Citadel

`citadel` assesses the resilience of a wallet or treasury across multiple dimensions.  `CitadelAssessmentService` gathers signals from UTXO hygiene and mempool risk, script analysis, policy evaluation, inheritance plan verification and sovereignty‑graph modelling to produce weighted scores and an overall resilience grade.  `RepairPlanService` uses these scores to generate prioritized remediation steps for operators.  Additional services in this package compute sovereignty graphs, verify inheritance paths and generate insights; collectively they help operators detect weaknesses and plan corrective actions.

### Market data and providers

`market_data` collects BTC prices and market data from multiple exchanges.  `MarketDataService` periodically polls provider implementations (Binance, Kraken, Bitstamp, Coinbase, etc.), normalizes their quotes, records them in the time‑series repository, and computes a median price and provider spread.  `aggregation.py` calculates confidence metrics by evaluating provider variance and median spread, while `provider_health.py` tracks the success/failure history of each provider and emits degraded or recovered events when their reliability changes.  A registry wires in new providers and exposes them to the rest of the system.

### Mempool and fee analytics

`mempool` models network congestion to inform fee recommendations.  `MempoolAnalyzerService` ingests mempool snapshots and block templates, computes backlog ratios and derives priority fee bands with associated confidence levels.  `FeeMarketModel` transforms these bands into recommended sat/vbyte fee rates for different confirmation targets.  `FeeAnalyticsService` in `analytics` wraps these insights, merges them with market data and surfaces user‑friendly fee recommendations and mempool status.

### Treasury

`treasury` orchestrates treasury actions such as withdrawal requests, chain‑state verification and policy checks.  `TreasuryService` evaluates each request against policy rules, checks chain state for RBF/CPFP possibilities, ensures operator approval and logs the action.  It publishes domain events (e.g., `treasury.request.evaluated`) and interacts with Citadel to factor resilience scores into risk evaluation.

### Event bus and domain events

`events` implements the internal eventing infrastructure.  `DomainEventPublisher` is a convenience wrapper for emitting typed domain events.  `EventBusService` persists events in an outbox, ensures idempotency, groups them by topic and dispatches them to configured webhooks and WebSocket subscribers.  This bus underpins asynchronous coordination across the platform: trace reports, citadel assessments, evidence packets, provider‑health changes and treasury actions all publish events that consumers can subscribe to.

### Observability and operations

`observability` provides operational insight.  `OperationsSnapshotService` aggregates provider health, chain state, mempool congestion, background job statuses and error counts to compute a runtime severity level and determine whether the system should enter degraded mode.  These snapshots feed dashboards and drive automated recovery or escalation.

### Intelligence and evidence

`intelligence` assembles multi‑source evidence.  `EvidencePacketBuilder` links news articles, market events, attribution diagnostics and narrative context into replayable evidence packets; it stores them and publishes an `evidence.packet.created` event.  Evidence packets are used by the market signal governance layer to justify signal publication and by the Market Time Machine UI for replay.

### Additional services

Other packages include `education` for static educational snippets, `analytics` for higher‑level analytics (such as fee recommendations), `ingestion` for scheduled jobs and `public_site` for the Market Time Machine and admin dashboards.  Each service publishes domain events and collaborates through the event bus, enabling decoupled yet coordinated functionality.

These services together form the heart of Bitcoin Bastion.  By composing specialized services and linking them through a shared event bus, the platform maintains clear boundaries between domains while enabling cross‑service workflows such as risk analysis feeding into treasury policy or mempool congestion informing fee recommendations and citadel resilience scores.

## How it works

At a high level the platform ingests market data and news from multiple providers, transforms them into canonical events, attributes price movements, and surfaces evidence‑rich intelligence:

- **Ingestion & normalization:** Price points, candles, news articles and mempool data are collected from multiple providers, deduplicated and normalized. Deterministic event clustering produces canonical news events and BTC candles.
- **Impact & attribution:** The candle attribution engine computes impact windows around BTC candles and ranks news events by confidence; impact diagnostics and delayed‑reaction detection highlight potential causes. Historical similarity compares current events and candles against seeded market patterns, generating reaction profiles and analog evidence.
- **Narratives & shock index:** The narrative heatmap engine classifies news into evolving narratives and generates heat/impact/dominance metrics; the shock index service quantifies combined market/narrative shock to highlight unusual market stress.
- **Evidence & governance:** Evidence packets record end‑to‑end state — migrations, schema parity, runtime health, provider quality, recovered evidence and deployment artifacts. The Market Signal Governance layer evaluates candidate signals against publishing policy and requires operator review before publication.
- **Event bus & plugin platform:** An internal event taxonomy, outbox and bus persist and dispatch domain events. Webhook and WebSocket services deliver signed notifications; the plugin API allows safe extensions with restrictive permissions.
- **User interfaces:** The web console provides dashboards for price context, shock index, similarity and narrative panels; the Market Time Machine UI shows timeline navigation, candle context, evidence replay and narrative heatmaps.

This layered architecture ensures that market intelligence remains evidence‑based, explainable and safe for self‑hosted environments.

## Installation and local development

A Makefile provides convenient targets for development.  Typical workflow:

```bash
git clone https://github.com/Hegehub/bitcoinbastion.git
cd bitcoinbastion
make install-dev      # install Python dependencies
cp .env.example .env  # configure local environment
make migrate          # run initial database migrations
make run              # start the application
```

Use `make lint`, `pytest -q`, `make migration-smoke`, `make docs-truthfulness` and `make ci-release-gates` to run verification gates before contributing.

For containerized development:

```bash
docker compose up -d --build
curl http://localhost:8000/api/v1/health/live
```

### Deployment options

Use [Deployment Methods](docs/DEPLOYMENT_METHODS.md) as the canonical decision
and command guide. It covers the repository-backed Compose, Kubernetes, K3s,
Kind, Minikube, constrained single-node, and bare-metal/systemd paths, including
their prerequisites, limitations, verification, and evidence requirements.
Profile metadata lives under `deploy/runtime-profiles`; the canonical Kubernetes
manifests live under `deploy/kubernetes`.

Rendering or applying repository manifests is not proof of a successful or
production-ready deployment. Promotion requires revision- and
environment-specific evidence described in
[PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

## License

This project is licensed under the **MIT License**.  See the [`LICENSE`](LICENSE) file for full details.  All contributions must preserve the no‑custody posture and must not weaken lint/tests/CI gates or hide degraded states.

## Contributing

Before submitting changes, review the contribution rules (section 26 in the original README).  Contributions must preserve no‑custody rules, avoid secrets, keep documentation synchronized with code, and require evidence for production claims.  See `docs/STATUS.md` and related documentation for the current readiness requirements.

## Known limitations

While Bitcoin Bastion provides extensive evidence‑driven insight, it does not make trading decisions or price predictions.  Historical similarity, candle attribution and narratives are informational only and should not be treated as guarantees.  External providers can be unavailable, and production readiness requires environment‑specific validation, backup/restore testing and operator sign‑off.

## Ongoing work and future modules

The repository continues to evolve beyond the baseline described above.  Key areas of development include:

- **Database expansion:** Alembic migrations have recently added a rich source registry and health tables for news providers, including attributes like homepage URL, country code, default confidence, failure backoff configuration and tags, plus a `source_health_records` table for latency and health metrics.  Additional migrations created the `market_pattern_library` and `historical_similarity_records` tables to seed deterministic market patterns and persist historical similarity results.  A subsequent migration expanded the narrative heatmap engine with a detailed taxonomy, keyword weights and observation tables.

- **Intelligence engines:** The Intelligence layer now includes a pattern library, pattern classification service and market memory service for deterministic pattern matching and reaction profiling.  The narrative heatmap engine has been expanded with a taxonomy of narratives and keywords that feed classification and dominance metrics.

- **News scoring and sentiment:** A local sentiment engine and market-news scoring service are being integrated for more granular event scoring and classification.


These ongoing modules are not yet production-ready and therefore are not all
documented in the main README. Contributors should use the canonical docs,
current route ownership, tests, and migration files instead of archived frontend
migration assumptions.

---

## 18. Observability

The project supports or plans observability through:

* `/metrics`;
* health endpoints;
* readiness endpoints;
* observability snapshots;
* provider-health evidence;
* recovery checks;
* Kubernetes ServiceMonitor;
* Prometheus rules;
* Grafana dashboards;
* Alertmanager routing;
* incident automation notes.

Production observability should track:

* API availability;
* readiness stability;
* degraded mode;
* provider fallback;
* provider confidence;
* Citadel runtime health;
* recovery findings;
* worker queue health;
* delivery failures;
* migration/evidence job status;
* backup status.

---

## 19. Backup, Restore, and DR

Production operations should include:

* PostgreSQL backup strategy;
* restore validation;
* PITR strategy if applicable;
* Redis recovery strategy;
* provider outage drill;
* delivery outage drill;
* recovery SLO drill;
* disaster recovery runbook;
* evidence retention policy.

Production restore must be explicit and operator-controlled.
No destructive restore should run automatically.

---

## 20. GitOps and Release Governance

Recommended production flow:

```text
dev → staging → evidence → approval → production
```

Promotion should be based on:

* immutable image digest;
* rendered Kubernetes manifests;
* passing local gates;
* passing staging deployment;
* migration evidence;
* schema parity evidence;
* release evidence;
* observability validation;
* operator approval.

Production should not use mutable `latest` images.

---

## 21. Supply Chain Security

Recommended controls:

* SBOM generation;
* vulnerability scanning;
* image signing;
* provenance;
* immutable image digests;
* admission policy examples;
* no unsigned production image unless explicitly accepted;
* no hidden vulnerability exceptions.

Possible tools:

* Syft;
* Trivy;
* Grype;
* pip-audit;
* Cosign;
* Kyverno;
* OPA Gatekeeper.

---

## 22. Runtime Security

Recommended Kubernetes runtime controls:

* least-privilege RBAC;
* restricted Pod Security;
* default-deny NetworkPolicy;
* controlled egress;
* emergency lockdown policy;
* secret leakage scanning;
* runtime detection examples;
* kube-bench;
* kube-score;
* Polaris;
* Falco rules.

Emergency lockdown should preserve observability where possible while blocking unsafe external communication.

---

## 23. Known Limitations

Bitcoin Bastion must remain honest about limitations.

Current or possible limitations:

* Citadel may include synthetic/baseline components.
* Protocol analytics are advisory, not consensus proof.
* Provider data can be stale, unavailable, or inconsistent.
* Telegram or delivery providers can fail.
* Kubernetes evidence requires actual cluster execution.
* Production SLOs require burn-in evidence.
* Backup/restore claims require real restore validation.
* Security policy examples are not the same as enforced cluster policy.
* GitOps templates are not proof of production deployment.

---

## 24. Roadmap

### Phase 1 — Backend hardening

* typed service/repository boundaries;
* stable schema models;
* migration smoke tests;
* docs truthfulness;
* release gates.

### Phase 2 — Evidence layer

* release evidence;
* PostgreSQL evidence;
* schema parity evidence;
* observability snapshot;
* provider-health evidence.

### Phase 3 — Kubernetes foundation

* API/worker/beat deployments;
* migration jobs;
* evidence jobs;
* NetworkPolicy;
* ServiceMonitor;
* staging/production overlays.

### Phase 4 — Kubernetes production hardening

* GitOps;
* External Secrets;
* Kyverno/OPA;
* Grafana dashboards;
* Alertmanager;
* KEDA;
* backup/restore;
* DR drills.

### Phase 5 — Supply chain security

* SBOM;
* vulnerability scanning;
* image signing;
* provenance;
* immutable image digest promotion.

### Phase 6 — Production RC

* staging deployment;
* evidence generation;
* operator sign-off;
* production cutover;
* burn-in;
* post-RC hardening.

---

## 25. Quick Command Reference

```bash
# Local checks
make lint
python -m pytest -q
make migration-smoke
make docs-truthfulness
make ci-release-gates

# Docker
docker compose up -d --build

# Kubernetes render
make k8s-render-dev
make k8s-render-staging
make k8s-render-production

# Kubernetes staging
make k8s-apply-staging
make k8s-status

# Evidence jobs
make k8s-run-migration
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
make k8s-run-release-evidence
make k8s-collect-evidence-artifacts

# Production promotion
make k8s-promotion-checklist
make k8s-production-approval-template
make k8s-apply-production

# Security / operations
make k8s-security-check
make k8s-secret-scan
make supply-chain-check
make k8s-operations-check
```

Some targets may depend on optional local tools. If a target is unavailable, consult the relevant documentation in `docs/` and `deploy/kubernetes/`.

---

## 26. Contribution Rules

Before contributing:

1. Preserve no-custody posture.
2. Do not add seed/private-key handling.
3. Do not hide degraded/fallback/synthetic states.
4. Do not weaken lint/tests/CI gates.
5. Do not commit secrets.
6. Do not claim production readiness without evidence.
7. Keep docs synchronized with actual code.
8. Prefer explicit operator control over silent automation.
9. Preserve Bitcoin-first design.
10. Keep deployment reproducible.

---

## 27. Final Production Decision Model

Final release decision must be evidence-based.

Possible states:

```text
NOT READY
PRE-RC / PRODUCTION-ORIENTED BETA
RC-ready pending environment evidence
PRODUCTION RELEASE CANDIDATE
```

A project may be called **Production Release Candidate** only if:

* local gates pass;
* Kubernetes render passes;
* staging evidence exists;
* PostgreSQL evidence exists;
* release evidence exists;
* security evidence is reviewed;
* operator sign-off exists;
* no P0 blockers remain.

---

## 28. License

License status: **TBD**.

Before production or public commercial use, define and commit a clear license.

---

## 29. Summary

Bitcoin Bastion is a Bitcoin-first, no-custody, evidence-driven backend platform for sovereign operational intelligence and production-grade deployment control.

Its strongest idea is simple:

> Do not trust silent systems.
> Make runtime, risk, deployment, and readiness visible, auditable, and operator-controlled.

Bitcoin Bastion is built to become a foundation for serious Bitcoin-native infrastructure where sovereignty, evidence, and operational discipline matter.

## Source Health
Provider confidence and degraded state tracking are implemented for news sources.

## Deduplication & Clustering Engine
Deterministic deduplication prevents duplicate-news spam and preserves replayable evidence for canonical event attribution.

- Market data provider layer for BTC/USD (Binance, Kraken, Coinbase, Bitstamp) with provider-aware aggregation and degraded-mode visibility.

- Market provider layer v2 added with median aggregation and degraded-state exposure.

- BTC candle evidence APIs now expose candle-level provider snapshot details.

- Added `/api/v1/market/health` snapshot for provider-count, degraded-state and confidence visibility.

- News scoring foundation: deterministic rule-based scoring with explainability and limitations (no OpenAI dependency).

- News scoring exposes explainable relevance, confidence, and narrative tags (informational only).

### Candle Attribution Engine

Bitcoin Bastion includes a replay-safe Candle Attribution Engine for Market Time
Machine. It ranks nearby news/events as possible BTC candle contributors using
configurable windows, weighted relevance/impact/provider/freshness/direction
factors, confidence bands, replay evidence, and operator review hooks. It always
treats attribution as correlation-based context, not causation or trading advice.

### Historical Similarity Engine

Bitcoin Bastion now includes a production Historical Similarity Engine for Market Time Machine. It classifies NewsEvents into deterministic market patterns, compares historical analogs across event type, sentiment, narrative category, impact score, BTC reaction windows, and confidence, and returns reaction statistics for operator review. Historical similarity is informational only: **Historical similarity does not guarantee future outcomes.**

- Narrative Heatmap: `docs/BMTM_NARRATIVE_HEATMAP.md` documents Bitcoin narrative taxonomy, heat scoring, dominance, history, and correlation-only safety limits.

- BMTM-034 Narrative Heatmap registry: `config/narratives.yaml` and `app/cli/seed_narratives.py` provide a local-first narrative registry and seed path for heatmap, trend, leaderboard, and narrative timeline API contracts.


### Historical Similarity Engine and Pattern Library

Bastion Market Time Machine now includes historical market memory: event pattern classification, similarity search, reaction statistics, pattern confidence, narrative memory fields, and frontend-ready APIs under `/api/v1/intelligence/similarity` and `/api/v1/intelligence/patterns`. Outputs are historical context only and explicitly avoid prediction or causation claims.

### Historical Similarity Engine and Narrative Memory

Bastion Market Time Machine now includes a finalized deterministic Historical Similarity Engine, seeded production Pattern Library, historical reaction statistics, and Narrative Memory snapshots. API output is frontend-ready and includes matched patterns, historical examples, reaction statistics, confidence breakdowns, narrative tags, and mandatory safety limitations. Historical comparisons are evidence-based references only, not price predictions or financial advice.

### Market Time Machine Web Dashboard

Bitcoin Bastion now exposes the Market Time Machine through a self-hosted FastAPI/Jinja2/HTMX/Alpine.js web dashboard at `/market-time-machine`, with timeline (`/intelligence/timeline`), evidence (`/evidence/{packet_id}`), and candle attribution (`/candles/{candle_id}`) pages. The dashboard is evidence-first, responsive, accessible, and display-only: it renders backend DTOs, shows provider/evidence limitations, and never presents historical context as price prediction or financial advice.

### Market Timeline and Candlestick Intelligence Dashboard

The primary Market Time Machine dashboard now lives at `/market`. It combines timeline navigation, BTC candles, deterministic news markers, candle context, attribution confidence, evidence overlays, historical similarity previews, and narrative strength. API contracts under `/api/v1/intelligence/timeline`, `/api/v1/intelligence/candles/{candle_id}`, and `/api/v1/intelligence/events/{event_id}/timeline` are frontend-ready and preserve correlation-not-causation, evidence-based, operator-reviewed, and confidence-score safety fields.

## Production observability and health

Bitcoin Bastion exposes operational health through `/api/v1/health`, `/api/v1/health/providers`, `/api/v1/health/jobs`, `/api/v1/health/runtime`, `/api/v1/health/degraded` and `/api/v1/metrics/status`. The monitoring philosophy is **no invisible failures**: degraded providers, delayed jobs, Telegram delivery failures, fallbacks and recovery lifecycle events must remain visible to operators and downstream confidence calculations.

### Operations control plane

The production control plane exposes root health probes (`/health/live`, `/health/ready`, `/health/startup`) plus dependency, provider, intelligence and operations health endpoints. Operators can use `/api/v1/operations/status`, `/api/v1/operations/drills`, `/api/v1/operations/metrics-summary`, and `/api/v1/operations/runbooks` for degraded-state visibility, recovery evidence, SLO summaries and runbook links.

### Disaster recovery validation

Disaster recovery validation is exposed through operational health DTOs and records backup verification, restore verification, deterministic replay validation and integrity verification. The system must not report readiness as healthy when required providers, timeline generation, database or scheduler checks are degraded.


## Release status

Current decision: **HOLD**. Historical production-candidate reports are retained
under `docs/archive/audits/2026/`; they describe earlier revisions and do not
override current failing gates. Public market-intelligence output must continue
to state that correlation is not proof of causation, analysis is informational,
and outputs are not financial advice.

## Developer and operator tools

- Python SDK: see [`sdk/python/README.md`](sdk/python/README.md).
- Operator-safe CLI: see [`docs/CLI.md`](docs/CLI.md).
- Bastion MCP Connector: see [`docs/MCP_CONNECTOR.md`](docs/MCP_CONNECTOR.md).
- TypeScript SDK: see [`docs/TYPESCRIPT_SDK.md`](docs/TYPESCRIPT_SDK.md) and [`sdk/typescript/README.md`](sdk/typescript/README.md).

### Plugin API foundation

Bitcoin Bastion now includes a safe Plugin API foundation for manifest-first, deny-by-default in-process extensions. See [`docs/PLUGIN_API.md`](docs/PLUGIN_API.md), [`docs/PLUGIN_PERMISSIONS.md`](docs/PLUGIN_PERMISSIONS.md), and [`docs/PLUGIN_SECURITY_MODEL.md`](docs/PLUGIN_SECURITY_MODEL.md). Plugins are not a custody interface, signing interface, transaction broadcaster, or marketplace runtime.

## Reflex-only frontend status (2026-06-29)

The old Next.js frontend directory has been removed. `frontend/` is now
the only repository-native frontend. FastAPI remains the backend source of
truth, and FastAPI/Jinja still owns delegated Market detail/dashboard routes.
The removal decision is preserved as historical evidence in
[`docs/archive/audits/2026/OLD_FRONTEND_REMOVAL_REPORT.md`](docs/archive/audits/2026/OLD_FRONTEND_REMOVAL_REPORT.md).

## Authentication

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled. Use the `/api/v1/access/*` payment, certificate, challenge, session, and signed-request flow instead of `/api/v1/auth/login` or bearer tokens.

Bastion will never ask for your Bitcoin seed or Bitcoin private key.

# Bitcoin Bastion

> **Bitcoin-first sovereign backend for evidence-driven market intelligence, operational resilience, and production-grade self-hosted deployment.**

[Website](https://bitcoin-bastion.com) • [Status Documentation](docs/STATUS.md) • [License](LICENSE)

![Status](https://img.shields.io/badge/status-Production%20Candidate%20--%2099%25%20readiness-blue)
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

The repository includes extensive documentation covering every major subsystem:

- **Historical Similarity Engine** – pattern matching, reaction profiles, similarity scoring and limitations (`docs/HISTORICAL_SIMILARITY_ENGINE.md`);
- **Market Signal Governance** – candidate lifecycle, publishing gates, operator review and delivery logs (`docs/MARKET_SIGNAL_GOVERNANCE.md`);
- **Evidence Packets & Replay** – replayable evidence bundles, lineage, integrity snapshots, timeline replay and exports (`docs/EVIDENCE_PACKETS.md`, `docs/EVIDENCE_REPLAY.md`);
- **Market Time Machine UI** – `/market` interface for BTC candles, news markers, evidence packets, historical similarity, replay timeline, shock index, narratives and provider health (`docs/MARKET_TIME_MACHINE_UI.md`);
- **Market Intelligence Dashboard** – web console for BTC price context, shock index, Market Time Machine, narratives, signals, evidence/replay and source quality;
- Additional production docs: `docs/STATUS.md`, `docs/PRODUCTION_READINESS.md`, `docs/OPERATIONS_RUNBOOK.md`, `docs/DEPLOYMENT_EVIDENCE_PACK.md`, `docs/FINAL_PRODUCTION_AUDIT.md`, `docs/SOVEREIGNTY_CERTIFICATION.md`, `docs/RELEASE_CANDIDATE_REPORT.md`, and others in the `docs/` directory.

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

## Current status (June 2026)

As of June 2026 the project is a production candidate and operationally hardened.  The Market Time Machine subsystem and the overall platform are approximately **99 % production‑ready**【turn8file0†L19-L23】.  Core ingestion, scoring, candle attribution, historical similarity, pattern memory, governance, evidence packets, narrative heatmaps, plugin API, internal event registry/outbox/bus and webhook management are implemented【turn8file0†L11-L17】【turn8file0†L27-L37】.  Remaining work is limited to environment‑specific production evidence such as live Kubernetes rendering, load testing, provider incident drills, Telegram runtime proof, penetration testing and accessibility certification【turn8file0†L19-L23】.  Consult `docs/STATUS.md` (audit dated 2026‑05‑23) for the latest readiness audit and detailed task breakdown【turn7file0†L1-L6】.

## Main components

The platform consists of multiple layers:

- **FastAPI backend** – exposes application APIs, health/readiness and admin endpoints, coordinates core services and collects release evidence.
- **Core services** – provider health, market/news intelligence, delivery logic, recovery checks, protocol advisory and Citadel evidence layer.
- **Data layer** – PostgreSQL with SQLAlchemy and Alembic migrations; supports migration smoke tests and schema parity validation.
- **Background runtime** – Celery workers and beat, Redis broker/cache and scheduled jobs for health collection, recovery checks and evidence tasks.
- **Evidence layer** – release evidence, migration smoke evidence, schema parity evidence, provider evidence, observability snapshot and deployment evidence pack.
- **Kubernetes runtime layer** – manifests for API/worker/beat deployments, migration/evidence jobs, CronJobs for provider health and recovery drills, NetworkPolicy, ServiceMonitor, GitOps templates and production runbooks.
- **Market Time Machine** – web dashboard `/market` providing timeline navigation, BTC candles, deterministically scored news markers, candle context, attribution confidence, historical similarity previews, narrative heatmap and shock index【turn1file0†L152-L162】【turn1file0†L160-L163】.
- **Event & plugin layer** – internal event taxonomy, outbox, bus and webhook management for safe notifications【turn8file0†L27-L37】【turn8file0†L49-L63】; plugin API foundation for deterministic extension points with restrictive sandbox defaults and audit records.

## Services directory

The `app/services` package contains the core domain services that implement the platform’s business logic.  Each service encapsulates a cohesive set of responsibilities and publishes domain events through the event bus.  At a high level:

### Bastion Trace

`bastion_trace` evaluates the risk associated with a Bitcoin transaction or UTXO.  `TraceService` coordinates a series of heuristics—including dust‑radar, false‑positive guards, UTXO hygiene checks, privacy shield lookups and payment‑context risk evaluations—to compute a **trace band** (low, medium, high).  It assembles a `TraceReport`, stores it, and publishes a `trace.report.created` event to the event bus for asynchronous consumers【turn48file0†L68-L97】.  A companion `LiteTraceReportService` maps trace bands to human‑readable labels and suggested operator actions【turn49file0†L9-L38】.

### Citadel

`citadel` assesses the resilience of a wallet or treasury across multiple dimensions.  `CitadelAssessmentService` gathers signals from UTXO hygiene and mempool risk, script analysis, policy evaluation, inheritance plan verification and sovereignty‑graph modelling to produce weighted scores and an overall resilience grade【turn50file0†L8-L24】【turn50file0†L66-L74】.  `RepairPlanService` uses these scores to generate prioritized remediation steps for operators【turn51file0†L69-L80】.  Additional services in this package compute sovereignty graphs, verify inheritance paths and generate insights; collectively they help operators detect weaknesses and plan corrective actions.

### Market data and providers

`market_data` collects BTC prices and market data from multiple exchanges.  `MarketDataService` periodically polls provider implementations (Binance, Kraken, Bitstamp, Coinbase, etc.), normalizes their quotes, records them in the time‑series repository, and computes a median price and provider spread【turn52file0†L18-L48】.  `aggregation.py` calculates confidence metrics by evaluating provider variance and median spread【turn54file0†L11-L31】, while `provider_health.py` tracks the success/failure history of each provider and emits degraded or recovered events when their reliability changes【turn55file0†L12-L34】.  A registry wires in new providers and exposes them to the rest of the system.

### Mempool and fee analytics

`mempool` models network congestion to inform fee recommendations.  `MempoolAnalyzerService` ingests mempool snapshots and block templates, computes backlog ratios and derives priority fee bands with associated confidence levels【turn61file0†L23-L77】.  `FeeMarketModel` transforms these bands into recommended sat/vbyte fee rates for different confirmation targets【turn62file0†L17-L45】.  `FeeAnalyticsService` in `analytics` wraps these insights, merges them with market data and surfaces user‑friendly fee recommendations and mempool status【turn65file0†L11-L33】.

### Treasury

`treasury` orchestrates treasury actions such as withdrawal requests, chain‑state verification and policy checks.  `TreasuryService` evaluates each request against policy rules, checks chain state for RBF/CPFP possibilities, ensures operator approval and logs the action.  It publishes domain events (e.g., `treasury.request.evaluated`) and interacts with Citadel to factor resilience scores into risk evaluation【turn60file0†L24-L67】【turn60file0†L106-L133】.

### Event bus and domain events

`events` implements the internal eventing infrastructure.  `DomainEventPublisher` is a convenience wrapper for emitting typed domain events【turn57file0†L17-L35】.  `EventBusService` persists events in an outbox, ensures idempotency, groups them by topic and dispatches them to configured webhooks and WebSocket subscribers【turn58file0†L61-L136】.  This bus underpins asynchronous coordination across the platform: trace reports, citadel assessments, evidence packets, provider‑health changes and treasury actions all publish events that consumers can subscribe to.

### Observability and operations

`observability` provides operational insight.  `OperationsSnapshotService` aggregates provider health, chain state, mempool congestion, background job statuses and error counts to compute a runtime severity level and determine whether the system should enter degraded mode【turn59file0†L52-L166】.  These snapshots feed dashboards and drive automated recovery or escalation.

### Intelligence and evidence

`intelligence` assembles multi‑source evidence.  `EvidencePacketBuilder` links news articles, market events, attribution diagnostics and narrative context into replayable evidence packets; it stores them and publishes an `evidence.packet.created` event【turn66file0†L39-L70】【turn66file0†L110-L152】.  Evidence packets are used by the market signal governance layer to justify signal publication and by the Market Time Machine UI for replay.

### Additional services

Other packages include `education` for static educational snippets【turn64file0†L6-L19】, `analytics` for higher‑level analytics (such as fee recommendations【turn65file0†L11-L33】), `ingestion` for scheduled jobs and `public_site` for the Market Time Machine and admin dashboards.  Each service publishes domain events and collaborates through the event bus, enabling decoupled yet coordinated functionality.

These services together form the heart of Bitcoin Bastion.  By composing specialized services and linking them through a shared event bus, the platform maintains clear boundaries between domains while enabling cross‑service workflows such as risk analysis feeding into treasury policy or mempool congestion informing fee recommendations and citadel resilience scores.

## How it works

At a high level the platform ingests market data and news from multiple providers, transforms them into canonical events, attributes price movements, and surfaces evidence‑rich intelligence:

- **Ingestion & normalization:** Price points, candles, news articles and mempool data are collected from multiple providers, deduplicated and normalized. Deterministic event clustering produces canonical news events and BTC candles.
- **Impact & attribution:** The candle attribution engine computes impact windows around BTC candles and ranks news events by confidence; impact diagnostics and delayed‑reaction detection highlight potential causes【turn8file0†L11-L17】. Historical similarity compares current events and candles against seeded market patterns, generating reaction profiles and analog evidence【turn8file0†L15-L17】.
- **Narratives & shock index:** The narrative heatmap engine classifies news into evolving narratives and generates heat/impact/dominance metrics; the shock index service quantifies combined market/narrative shock to highlight unusual market stress【turn8file0†L11-L17】.
- **Evidence & governance:** Evidence packets record end‑to‑end state — migrations, schema parity, runtime health, provider quality, recovered evidence and deployment artifacts. The Market Signal Governance layer evaluates candidate signals against publishing policy and requires operator review before publication【turn21file0†L20-L33】.
- **Event bus & plugin platform:** An internal event taxonomy, outbox and bus persist and dispatch domain events. Webhook and WebSocket services deliver signed notifications; the plugin API allows safe extensions with restrictive permissions【turn19file0†L5-L17】【turn19file0†L35-L43】.
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

For Kubernetes deployment, see `deploy/kubernetes` and `docs/PRODUCTION_READINESS.md` for rendering and applying manifests, running evidence jobs and promotion checklists.

## License

This project is licensed under the **MIT License**【turn2file0†L3-L13】.  See the [`LICENSE`](LICENSE) file for full details.  All contributions must preserve the no‑custody posture and must not weaken lint/tests/CI gates or hide degraded states.

## Contributing

Before submitting changes, review the contribution rules (section 26 in the original README).  Contributions must preserve no‑custody rules, avoid secrets, keep documentation synchronized with code, and require evidence for production claims【turn0file1†L926-L933】.  See `docs/STATUS.md` and related documentation for the current readiness requirements.

## Known limitations

While Bitcoin Bastion provides extensive evidence‑driven insight, it does not make trading decisions or price predictions.  Historical similarity, candle attribution and narratives are informational only and should not be treated as guarantees【turn1file0†L160-L167】.  External providers can be unavailable, and production readiness requires environment‑specific validation, backup/restore testing and operator sign‑off【turn0file1†L803-L817】.

## Ongoing work and future modules

The repository continues to evolve beyond the baseline described above.  Key areas of development include:

- **Database expansion:** Alembic migrations have recently added a rich source registry and health tables for news providers, including attributes like homepage URL, country code, default confidence, failure backoff configuration and tags, plus a `source_health_records` table for latency and health metrics【turn85file0†L19-L31】.  Additional migrations created the `market_pattern_library` and `historical_similarity_records` tables to seed deterministic market patterns and persist historical similarity results【turn86file0†L41-L76】.  A subsequent migration expanded the narrative heatmap engine with a detailed taxonomy, keyword weights and observation tables【turn87file0†L17-L48】.

- **Intelligence engines:** The Intelligence layer now includes a pattern library, pattern classification service and market memory service for deterministic pattern matching and reaction profiling【turn78file0†L134-L144】【turn78file0†L149-L152】.  The narrative heatmap engine has been expanded with a taxonomy of narratives and keywords that feed classification and dominance metrics【turn87file0†L17-L48】.

- **News scoring and sentiment:** A local sentiment engine and market-news scoring service are being integrated for more granular event scoring and classification.

- **Frontend migration to Reflex:** A parallel `reflex_frontend/` directory contains an experimental Python‑first webapp built with the Reflex framework【turn72file0†L5-L13】.  This frontend runs alongside the legacy Next.js frontend until route parity, API parity and production evidence are complete【turn82file0†L5-L11】.  Migration baselines and route inventories for Trace Lite, Market Time Machine and Market Intelligence are documented in `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md`【turn76file0†L11-L25】, and design system details are captured in `reflex_frontend/docs/DESIGN_SYSTEM.md`【turn84file0†L5-L17】.  The Next.js frontend remains frozen except for safety, broken route and documentation fixes【turn82file0†L26-L38】, while new features are added in Reflex.  Ensure that any new user‑facing functionality includes advisory copy, no‑custody warnings and degraded‑state visibility, consistent with Reflex docs and tests.

These ongoing modules are not yet fully production-ready and therefore not all documented in the main README.  Contributors should refer to the associated docs and migration files when working on these features, and avoid making major changes to the legacy frontend until cutover gates are met.

---

This updated README further refreshes the current status, expands the high‑level system overview, highlights how key subsystems interact, provides a detailed explanation of the services directory and summarizes ongoing development work, while maintaining clarity on scope, design principles and limitations.

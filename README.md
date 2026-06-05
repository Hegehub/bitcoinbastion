[Main README](README.md) · [License](LICENSE) · [Certificate](CERTIFICATE.md)
# Bitcoin Bastion

> **Bitcoin-first sovereign backend for evidence-driven market intelligence, operational resilience, and production-grade self-hosted deployment.**

- Website (Vercel): https://bitcoin-bastion.vercel.app
- Primary domain: https://bitcoin-bastion.com
- License: MNT (repo license file: MIT)

![Status](https://img.shields.io/badge/status-RC--ready%20pending%20environment%20evidence-orange)
![Bitcoin First](https://img.shields.io/badge/bitcoin-first-f7931a)
![No Custody](https://img.shields.io/badge/no--custody-enforced-brightgreen)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Kubernetes](https://img.shields.io/badge/kubernetes-supported-326ce5)
![License](https://img.shields.io/badge/license-MNT-informational)

---

## Core documentation

- Historical Similarity Foundation: `docs/HISTORICAL_SIMILARITY_ENGINE.md` documents pattern matching, reaction profiles, similarity scoring, limitations, and API contracts.
- Market Signal Governance: `docs/MARKET_SIGNAL_GOVERNANCE.md` documents candidate lifecycle, publishing policy gates, operator review, delivery logs, and no-causation safety.
- Evidence Packets and Replay: `docs/EVIDENCE_PACKETS.md` and `docs/EVIDENCE_REPLAY.md` document replayable evidence bundles, lineage, integrity snapshots, timeline replay, exports, and no-causation safety.
- Market Time Machine UI: `docs/MARKET_TIME_MACHINE_UI.md` documents the `/market` interface for BTC candles, news markers, candle explanations, evidence packets, historical similarity, replay timeline, shock index, narratives, and provider health.
- Market Intelligence Dashboard: `/market` provides the web intelligence console for BTC price context, News Shock Index, Market Time Machine, narratives, signals, evidence/replay, and source quality without trading-terminal or financial-advice framing.

- `docs/STATUS.md`
- `docs/PRODUCTION_READINESS.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/DEPLOYMENT_EVIDENCE_PACK.md`
- `docs/FINAL_PRODUCTION_GAP_AUDIT.md`
- `docs/KUBERNETES_RC_CERTIFICATION.md`
- `docs/FINAL_PRODUCTION_AUDIT.md`
- `docs/SOVEREIGNTY_CERTIFICATION.md`
- `docs/RELEASE_CANDIDATE_REPORT.md`

## 1. What is Bitcoin Bastion?

**Bitcoin Bastion** is a Bitcoin-first backend platform designed to help operators, builders, analysts, and future Bitcoin-native systems work with market intelligence, provider evidence, operational readiness, and deployment verification in a controlled, auditable way.

The project is not a wallet.
The project is not a custodian.
The project is not a trading bot that blindly executes actions.
The project is not a consensus replacement.

Bitcoin Bastion is a **sovereignty-grade backend foundation** for:

* Bitcoin market/news intelligence;
* provider-health monitoring;
* explainable runtime status;
* Citadel risk/evidence analysis;
* operational recovery checks;
* deployment evidence collection;
* Kubernetes-based production control;
* no-custody Bitcoin-aligned infrastructure.

Its main purpose is to make Bitcoin-related backend systems more:

* transparent;
* auditable;
* reproducible;
* self-hostable;
* operationally safe;
* evidence-driven;
* resistant to silent failure.

---

## 2. Core Philosophy

Bitcoin Bastion follows a strict set of design principles.

| Principle                     | Meaning                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Bitcoin-first**             | Bitcoin is the primary design reference. Other assets, if ever supported, must remain isolated and optional. |
| **No custody**                | The system must not hold, request, store, derive, or transmit seed phrases or private keys.                  |
| **Operator control**          | Risky actions require explicit operator awareness and approval.                                              |
| **Evidence over claims**      | Runtime state, deployment readiness, and provider quality must be backed by artifacts.                       |
| **Local/self-hosted capable** | The system should be deployable on a VPS, bare metal, homelab, or private Kubernetes cluster.                |
| **No black-box trust**        | External providers must be treated as fallible and observable.                                               |
| **Explicit limitations**      | Synthetic, advisory, degraded, fallback, and baseline states must remain visible.                            |
| **Rollback discipline**       | Production deployment must have a documented rollback path.                                                  |
| **Auditability**              | Release decisions should be explainable and supported by evidence.                                           |

---

## 3. What Bitcoin Bastion Is Not

Bitcoin Bastion intentionally avoids dangerous or misleading roles.

It is **not**:

* a custodial wallet;
* a seed phrase manager;
* a private key storage service;
* a fully automated trading executor;
* a financial advisor;
* a Bitcoin consensus replacement;
* a mining/Stratum system;
* a centralized SaaS dependency;
* a system that hides degraded state.

Any future feature that touches funds, signing, wallet operations, or Bitcoin transaction creation must preserve the **no-custody** model and require strict human confirmation.

---

## 4. High-Level Architecture

```text
Bitcoin Bastion
│
├── FastAPI Backend
│   ├── API routes
│   ├── health/readiness endpoints
│   ├── admin/status endpoints
│   ├── observability endpoints
│   └── metrics endpoint
│
├── Core Services
│   ├── provider health
│   ├── market/news intelligence
│   ├── delivery logic
│   ├── recovery checks
│   ├── protocol advisory layer
│   └── Citadel risk/evidence layer
│
├── Data Layer
│   ├── PostgreSQL
│   ├── SQLAlchemy
│   ├── Alembic migrations
│   └── schema parity validation
│
├── Background Runtime
│   ├── Celery worker
│   ├── Celery beat
│   ├── Redis broker/cache
│   └── scheduled jobs
│
├── Evidence Layer
│   ├── release evidence
│   ├── migration smoke evidence
│   ├── schema parity evidence
│   ├── provider evidence
│   ├── observability snapshot
│   └── deployment evidence pack
│
└── Kubernetes Runtime Layer
    ├── API deployment
    ├── worker deployment
    ├── beat deployment
    ├── migration jobs
    ├── evidence jobs
    ├── provider-health CronJobs
    ├── recovery drill CronJobs
    ├── NetworkPolicy
    ├── ServiceMonitor
    ├── GitOps templates
    ├── security policies
    └── production runbooks
```

---

## 5. Main Components

### 5.1 FastAPI Backend

The backend exposes application APIs, health checks, readiness checks, observability endpoints, and administrative status endpoints.

Typical responsibilities:

* serve API requests;
* expose `/metrics`;
* expose health/readiness status;
* provide runtime status;
* coordinate service-layer operations;
* support release evidence collection.

---

### 5.2 PostgreSQL Persistence

Bitcoin Bastion uses PostgreSQL as the production-grade persistence target.

The repository includes migration and validation tooling for:

* Alembic migrations;
* migration smoke checks;
* schema parity checks;
* PostgreSQL staging validation;
* deployment evidence artifacts.

Required evidence artifacts include:

```text
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
```

---

### 5.3 Redis + Celery

Redis and Celery are used for asynchronous background execution.

Typical background responsibilities:

* provider health collection;
* scheduled recovery checks;
* delivery jobs;
* evidence-related tasks;
* operational checks;
* future drill execution.

---

### 5.4 Provider Health Layer

External providers are treated as fallible.

The provider-health layer is responsible for:

* tracking provider availability;
* tracking provider confidence;
* detecting fallback/mock states;
* exposing provider evidence;
* supporting degraded-mode visibility;
* feeding observability and release evidence.

The system should never silently trust a single external source.

---

### 5.5 Citadel Layer

The **Citadel** layer is an advisory risk/evidence layer.

It may include:

* runtime risk assessment;
* recovery readiness indicators;
* synthetic/baseline labeling;
* confidence penalties;
* provider evidence correlation;
* operator guidance;
* limitations and warning surfaces.

Important:

> Citadel is advisory. It is not Bitcoin consensus. It must not be described as a source of final truth.

---

### 5.6 Protocol Advisory Layer

Bitcoin-related protocol analysis is treated as advisory.

The system may analyze or surface:

* chain-state related signals;
* provider corroboration;
* finality/reorg-related risk indicators;
* protocol warnings;
* external provider consistency.

Important:

> Protocol analytics are not consensus proof. Bitcoin consensus remains with Bitcoin nodes and the Bitcoin protocol itself.

---

### 5.7 Evidence Layer

Bitcoin Bastion is designed around evidence-based readiness.

Expected release evidence may include:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
artifacts/sbom.spdx.json
artifacts/sbom.cyclonedx.json
artifacts/vulnerability_report.json
artifacts/provenance.json
```

Evidence should include, where available:

* git SHA;
* image digest;
* environment;
* timestamp;
* health status;
* readiness status;
* migration result;
* schema parity result;
* observability snapshot;
* provider health summary;
* known limitations;
* operator acknowledgement.

---

## 6. Kubernetes Runtime Control Plane

Bitcoin Bastion supports Kubernetes as a **sovereign runtime control plane**.

Kubernetes is used for:

* reproducible deployment;
* runtime isolation;
* health/readiness enforcement;
* migration jobs;
* evidence jobs;
* provider-health CronJobs;
* recovery drill CronJobs;
* observability;
* NetworkPolicy;
* GitOps promotion;
* rollback discipline;
* production runbooks.

Kubernetes is not used to create cloud lock-in.
The deployment should remain compatible with self-hosted clusters, VPS clusters, homelabs, and private infrastructure.

---

## 7. Kubernetes Capabilities

The Kubernetes layer may include:

| Capability                | Purpose                                          |
| ------------------------- | ------------------------------------------------ |
| `Deployment`              | API, worker, beat runtime                        |
| `Job`                     | migrations, evidence generation, validation      |
| `CronJob`                 | provider-health checks, recovery drills, backups |
| `ConfigMap`               | non-secret configuration                         |
| `Secret` / ExternalSecret | secret injection without committing credentials  |
| `NetworkPolicy`           | network blast-radius reduction                   |
| `ServiceMonitor`          | Prometheus scraping                              |
| `HPA` / KEDA              | scaling API/workers                              |
| GitOps                    | controlled promotion dev → staging → production  |
| Kyverno / OPA examples    | policy-as-code guardrails                        |
| Grafana dashboards        | operational visibility                           |
| Alertmanager routing      | incident notification                            |
| Backup/restore jobs       | operational recovery                             |
| DR drills                 | failure simulation                               |
| Evidence archive          | release auditability                             |

---

## 8. Repository Structure

Typical repository layout:

```text
.
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── tasks/
│
├── scripts/
│   ├── collect_release_evidence.py
│   ├── run_postgres_migration_smoke.py
│   └── check_postgres_schema_parity.py
│
├── deploy/
│   └── kubernetes/
│       ├── base/
│       ├── overlays/
│       ├── gitops/
│       ├── security/
│       ├── observability/
│       ├── autoscaling/
│       ├── evidence/
│       ├── rollout/
│       ├── backup/
│       ├── drills/
│       └── operations/
│
├── docs/
│   ├── STATUS.md
│   ├── PRODUCTION_READINESS.md
│   ├── FINAL_PRODUCTION_GAP_AUDIT.md
│   ├── DEPLOYMENT_EVIDENCE_PACK.md
│   ├── OPERATIONS_RUNBOOK.md
│   └── ...
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 9. Current Status

Current intended status:

```text
RC-ready pending environment evidence
```

This means:

* code quality gates may pass;
* Kubernetes manifests may exist;
* evidence jobs may exist;
* production-oriented documentation may exist;
* but final RC status still requires real environment evidence.

A full **Production Release Candidate** decision should only be declared after:

```bash
make lint
python -m pytest -q
make migration-smoke
make docs-truthfulness
make ci-release-gates
```

and after target-environment evidence artifacts are generated and reviewed.

---

## 10. Local Development

### 10.1 Clone

```bash
git clone https://github.com/Hegehub/bitcoinbastion.git
cd bitcoinbastion
```

### 10.2 Install

```bash
make install-dev
```

If the Makefile target is unavailable, use the repository-specific Python installation flow.

### 10.3 Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set required local values.

Never commit real secrets.

### 10.4 Run migrations

```bash
make migrate
```

### 10.5 Run application

```bash
make run
```

---

## 11. Local Verification

Run the standard verification gates:

```bash
make lint
python -m pytest -q
make migration-smoke
make docs-truthfulness
make ci-release-gates
```

Expected production-grade behavior:

* lint passes;
* mypy passes;
* tests pass;
* migration smoke passes;
* docs truthfulness passes;
* CI release gates pass.

If any of these fail, the project should not be marked as RC.

---

## 12. Docker / Compose

For local containerized execution:

```bash
docker compose up -d --build
```

Then check service health:

```bash
docker compose ps
```

If available:

```bash
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
curl http://localhost:8000/metrics
```

---

## 13. Kubernetes Deployment

### 13.1 Render manifests

```bash
make k8s-render-dev
make k8s-render-staging
make k8s-render-production
```

Or directly:

```bash
kubectl kustomize deploy/kubernetes/overlays/dev
kubectl kustomize deploy/kubernetes/overlays/staging
kubectl kustomize deploy/kubernetes/overlays/production
```

### 13.2 Apply staging

```bash
make k8s-apply-staging
make k8s-status
```

### 13.3 Run migration and evidence jobs

```bash
make k8s-run-migration
make k8s-run-postgres-migration-smoke
make k8s-run-postgres-schema-parity
make k8s-run-release-evidence
make k8s-collect-evidence-artifacts
```

Expected artifacts:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
```

### 13.4 Production promotion

Before production promotion:

```bash
make k8s-promotion-checklist
make k8s-production-approval-template
```

Then apply production only after evidence and approval:

```bash
make k8s-apply-production
make k8s-status
```

---

## 14. Production Readiness Gates

A production release candidate requires:

| Gate                          | Required               |
| ----------------------------- | ---------------------- |
| Lint                          | PASS                   |
| Mypy                          | PASS                   |
| Tests                         | PASS                   |
| Migration smoke               | PASS                   |
| Docs truthfulness             | PASS                   |
| CI release gates              | PASS                   |
| Kubernetes render             | PASS                   |
| PostgreSQL staging validation | PASS                   |
| Release evidence              | PRESENT                |
| Schema parity evidence        | PRESENT                |
| Observability validation      | PASS                   |
| Backup strategy               | DOCUMENTED / VALIDATED |
| Rollback plan                 | DOCUMENTED             |
| Operator sign-off             | PRESENT                |
| No-custody posture            | PRESERVED              |

---

## 15. Evidence Artifacts

Important artifacts:

```text
artifacts/release_evidence.json
artifacts/postgres_migration_smoke.json
artifacts/postgres_schema_parity.json
artifacts/sbom.spdx.json
artifacts/sbom.cyclonedx.json
artifacts/vulnerability_report.json
artifacts/provenance.json
```

These artifacts support:

* release auditability;
* deployment reproducibility;
* production readiness decisions;
* incident review;
* rollback analysis;
* operator sign-off.

---

## 16. Security Model

Bitcoin Bastion security posture includes:

* no custody;
* no seed phrase handling;
* no private key handling;
* no silent provider trust;
* explicit fallback/degraded states;
* strict environment configuration;
* Kubernetes NetworkPolicy;
* non-root containers;
* resource limits;
* secret separation;
* optional External Secrets integration;
* optional Kyverno/OPA policy-as-code;
* optional image signing and SBOM generation;
* evidence-based release process.

---

## 17. No-Custody Rules

The following must remain true:

* Do not request seed phrases.
* Do not store seed phrases.
* Do not transmit seed phrases.
* Do not request private keys.
* Do not store private keys.
* Do not sign Bitcoin transactions automatically.
* Do not execute financial actions without explicit operator approval.
* Do not hide risk state from the operator.

If wallet or transaction-related functionality is ever added, it must be designed around:

* watch-only mode;
* PSBT-first workflows;
* external signing;
* explicit human confirmation;
* audit logs;
* policy enforcement.

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

Bitcoin Bastion includes a replay-safe Candle Attribution Engine foundation for Market Time Machine. It ranks nearby news events for a BTC candle using BTC relevance, market-impact score, provider/source confidence, time distance, and sentiment/candle direction matching while preserving the limitation that correlation is not proof of causation.

### Candle Attribution Engine

Bitcoin Bastion includes a production Candle Attribution Engine that ranks nearby news/events as possible BTC candle contributors with configurable windows, weighted scoring, confidence bands, replay evidence, and operator review hooks. It always treats attribution as correlation-based context, not causation or trading advice.

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


## Final production candidate certification

Bitcoin Bastion and Bastion Market Time Machine are classified as a conservative Production Candidate after the final repository-wide audit. The final reports are `docs/FINAL_PRODUCTION_AUDIT.md`, `docs/SOVEREIGNTY_CERTIFICATION.md`, and `docs/RELEASE_CANDIDATE_REPORT.md`. Public market-intelligence output must continue to display: Correlation is not proof of causation. Evidence-based informational analysis. Not financial advice.

This repository does not claim perfect security, guaranteed outcomes, or bug-free behavior. Environment-specific production validation remains required for Kubernetes rendering, load testing, Telegram runtime evidence, WAF/CDN/TLS/rate limiting, penetration testing, and accessibility certification.

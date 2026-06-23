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

---

This updated README further refreshes the current status, expands the high‑level system overview, and highlights how key subsystems interact while maintaining clarity on scope, design principles and limitations.

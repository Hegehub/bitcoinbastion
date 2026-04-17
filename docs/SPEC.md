# Bitcoin Bastion SPEC

## Product statement
Bitcoin Bastion is a **Bitcoin Sovereign Intelligence, Decision, and Operations Platform**. It is designed as a modular monolith that ingests ecosystem signals, interprets them with explainability artifacts, and delivers actionable recommendations for self-custody users, analysts, and treasury operators.

## Core capability map

### Intelligence domains
1. News Intelligence
2. On-chain Intelligence
3. Entity / OSINT Intelligence
4. Signal Engine

### Decision & operations domains
5. Wallet Health
6. Treasury / PSBT Workflows
7. Fee / UTXO Analytics
8. Privacy Risk Scoring
9. Policy-as-Code checks

### Delivery & platform domains
10. Telegram Delivery
11. REST API / Dashboard backend
12. Observability / Audit

## Reference architecture
Use a **modular monolith first** with explicit boundaries:
- `app/api`: transport layer, auth guards, schemas, request lifecycle
- `app/services`: orchestration and business workflows
- `app/db/repositories`: persistence contracts and implementations
- `app/integrations`: provider adapters and external APIs
- `app/tasks`: retry-safe asynchronous execution
- `app/services/explainability`: score explanations, evidence, provenance
- `app/services/policy`: policy evaluation and policy execution logs
- `app/services/observability`: runtime metrics, health, and ops reporting

## Functional requirements
- Ingest and normalize Bitcoin-relevant sources
- Deduplicate and cluster items into interpretable units
- Compute relevance/significance/confidence scores
- Build explainable signals with evidence lineage
- Publish feeds and digests to API and Telegram surfaces
- Score wallet health and privacy posture
- Track treasury requests and policy validation outcomes
- Persist audit-friendly records for sensitive actions

## Non-functional requirements
- Fully typed Python code (mypy-friendly)
- Thin handlers and thin routes
- Retry-safe jobs with provider failure tolerance
- Structured logs, metrics, health probes, request IDs
- Env-based configuration and secrets only
- Operator-grade reliability and extensibility

## API baseline (versioned)
- `/api/v1/health`
- `/api/v1/auth`
- `/api/v1/news`
- `/api/v1/signals`
- `/api/v1/onchain`
- `/api/v1/entities`
- `/api/v1/wallet`
- `/api/v1/fees`
- `/api/v1/treasury`
- `/api/v1/admin`
- `/api/v1/users`
- `/api/v1/privacy`
- `/api/v1/policy`
- `/api/v1/education`
- `/api/v1/observability`

## Telegram baseline
Required user commands:
- `/start`, `/help`, `/latest`, `/top`, `/digest`, `/watchlist`, `/fees`, `/wallet_health`, `/status`

Required admin commands:
- `/admin_publish`, `/admin_refresh`, `/admin_reprocess`, `/admin_sources`, `/admin_jobs`

## Roadmap framing
- **Phase A** foundation and toolchain hardening
- **Phase B** intelligence core (news + signal baseline)
- **Phase C** auth/treasury/privacy depth
- **Phase D** provider depth, policy runtime, evidence graph maturity
- **Phase E** production hardening, CI gates, readiness standards

# Bitcoin Bastion Platform Layers

This directory is a non-breaking architectural index for the platform. It groups the repository by operational responsibility without moving the existing application packages or changing import paths.

The active FastAPI runtime continues to live under `app/`. Existing routers, services, models, migrations, deployment files, documentation and tests remain valid. New implementation work can be staged under the matching layer folder below and then wired into the canonical runtime deliberately.

## Layer naming convention

- Use lowercase kebab-case directory names.
- Keep abbreviations explicit: `ci-cd`, `api-gateway`, `rbac-abac`, `ml-analytics-layer`.
- Do not store secrets in this tree. The `secrets` layer documents secret handling only.
- Prefer README-first changes before moving executable code.

## Canonical layers

| Layer | Directory | Primary responsibility |
| --- | --- | --- |
| Frontend | `platform/frontend` | User interfaces, web apps, console surfaces and frontend contracts. |
| Backend | `platform/backend` | FastAPI application composition, domain services and API runtime boundaries. |
| Database | `platform/database` | PostgreSQL schema, SQLAlchemy models, Alembic migrations and database checks. |
| Cache | `platform/cache` | Redis cache strategy, TTL policy and cache invalidation contracts. |
| Queue | `platform/queue` | Broker contracts and asynchronous queue topology. |
| Workers | `platform/workers` | Celery/background consumers and long-running job processors. |
| Scheduler | `platform/scheduler` | Periodic jobs, Celery beat, cron-style jobs and recovery drills. |
| Auth | `platform/auth` | Authentication, identity, access tokens and proof-of-access boundaries. |
| Object storage | `platform/object-storage` | S3/MinIO artifact storage, evidence packs and retention policy. |
| Search | `platform/search` | Search indexes, query surfaces and discovery services. |
| CI/CD | `platform/ci-cd` | GitHub Actions, release gates, build verification and deployment automation. |
| Docker | `platform/docker` | Container images, Compose profiles and local runtime packaging. |
| Monitoring | `platform/monitoring` | Metrics, probes, ServiceMonitor definitions and SLO signals. |
| Logging | `platform/logging` | Structured logs, request IDs and log shipping contracts. |
| Alerts | `platform/alerts` | Alert rules, escalation policy and incident notifications. |
| Backup | `platform/backup` | Backup plans, restore drills and retention evidence. |
| Secrets | `platform/secrets` | Secret injection policy, rotation and non-committed configuration. |
| Security | `platform/security` | Hardening, threat model, supply-chain checks and safe defaults. |
| Admin panel | `platform/admin-panel` | Operator/admin UI, protected workflows and support tooling. |
| Docs | `platform/docs` | Documentation ownership, truthfulness gates and architecture records. |
| Tests | `platform/tests` | Test strategy, fixtures, smoke tests and release evidence checks. |
| API gateway | `platform/api-gateway` | External ingress, routing, rate limits and edge policy. |
| Service mesh | `platform/service-mesh` | East-west traffic policy, mTLS and internal service routing. |
| Event bus | `platform/event-bus` | Domain events, outbox, internal bus and webhook/event delivery. |
| Distributed tracing | `platform/distributed-tracing` | Trace context propagation and span collection. |
| Observability stack | `platform/observability-stack` | Metrics, logs, traces, dashboards and evidence snapshots. |
| Audit logs | `platform/audit-logs` | Immutable operator/security audit events and audit exports. |
| RBAC/ABAC | `platform/rbac-abac` | Role-, attribute- and policy-based authorization. |
| Feature flags | `platform/feature-flags` | Runtime feature gates, rollout controls and kill switches. |
| Multi-region infra | `platform/multi-region-infra` | Regional deployment topology, failover and data placement. |
| Disaster recovery | `platform/disaster-recovery` | DR runbooks, RTO/RPO targets and recovery validation. |
| Zero-trust networking | `platform/zero-trust-networking` | Identity-aware network access, least privilege and segmented connectivity. |
| Policy engine | `platform/policy-engine` | Centralized policy decisions and operator-governed enforcement. |
| Data warehouse | `platform/data-warehouse` | Analytical storage, historical aggregates and reporting datasets. |
| ML/analytics layer | `platform/ml-analytics-layer` | Analytical models, intelligence scoring and model governance. |
| Compliance layer | `platform/compliance-layer` | Compliance controls, evidence mapping and policy attestations. |
| Internal developer platform | `platform/internal-developer-platform` | Developer workflows, templates, golden paths and self-service operations. |

## Current-code mapping

This layer tree is an architecture map, not a replacement for existing paths. Current canonical code remains in:

- `app/main.py` for FastAPI application composition.
- `app/api/` for HTTP routers and middleware.
- `app/services/` for domain services.
- `app/models/` and `alembic/` for database models and migrations.
- `app/tasks/` for background tasks and scheduling.
- `deploy/`, `docker/`, `Dockerfile` and Compose files for runtime packaging.
- `docs/` for production documentation and evidence.
- `tests/` for verification.

When a layer becomes mature enough to own executable code directly, move code in a separate migration PR and update imports/tests in the same change.
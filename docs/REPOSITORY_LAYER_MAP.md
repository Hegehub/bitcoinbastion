# Repository Layer Map

This document explains the non-breaking reorganization introduced by `platform/`.

## Why this exists

Bitcoin Bastion already has a working FastAPI/runtime layout. Moving `app/`, routers, models, tasks or deployment files directly would be a high-risk refactor because imports and runtime entrypoints are active. The `platform/` tree therefore acts as an architectural map first:

1. it creates stable names for major platform responsibilities;
2. it gives each layer a place for ownership notes and future implementation plans;
3. it preserves current imports, routers, tests and deployment paths;
4. it gives future PRs a safe target for staged migrations.

## New layer tree

The canonical layer index is `platform/README.md` and the machine-readable manifest is `platform/layers.yaml`.

Normalized layer directories:

- `platform/frontend`
- `platform/backend`
- `platform/database`
- `platform/cache`
- `platform/queue`
- `platform/workers`
- `platform/scheduler`
- `platform/auth`
- `platform/object-storage`
- `platform/search`
- `platform/ci-cd`
- `platform/docker`
- `platform/monitoring`
- `platform/logging`
- `platform/alerts`
- `platform/backup`
- `platform/secrets`
- `platform/security`
- `platform/admin-panel`
- `platform/docs`
- `platform/tests`
- `platform/api-gateway`
- `platform/service-mesh`
- `platform/event-bus`
- `platform/distributed-tracing`
- `platform/observability-stack`
- `platform/audit-logs`
- `platform/rbac-abac`
- `platform/feature-flags`
- `platform/multi-region-infra`
- `platform/disaster-recovery`
- `platform/zero-trust-networking`
- `platform/policy-engine`
- `platform/data-warehouse`
- `platform/ml-analytics-layer`
- `platform/compliance-layer`
- `platform/internal-developer-platform`

## Migration policy

Use this sequence for future physical moves:

1. Update the target layer README with ownership and boundary rules.
2. Move a narrow package or file group in one PR.
3. Update imports, route registration and deployment entrypoints in the same PR.
4. Add or update tests proving the new path works.
5. Update `platform/layers.yaml` and this document when the canonical path changes.

## Current non-breaking status

This change does not move existing executable code. It adds an organizational skeleton and documentation only. Current canonical runtime files remain in `app/`, `deploy/`, `docker/`, `docs/`, `tests/`, `scripts/`, `sdk/`, `alembic/` and root-level build files.

# Bitcoin Bastion — Implementation Status (as of 2026-04-14)

## 1) Where the project is now

Current state: **Phase 1 baseline is implemented**, with partial scaffolding for later modules.

Implemented and running in codebase:
- FastAPI modular API with `/api/v1/*` groups, middleware, metrics and error envelopes.
- SQLAlchemy models + repositories + Alembic migrations.
- Celery task skeleton for ingestion/delivery/ops.
- Core services for auth, ingestion, scoring, signaling, wallet/fee/treasury primitives.
- Docker/CI/test baseline.

## 2) Prompt alignment check

### Fully aligned (baseline)
- Modular monolith boundaries (`api`, `services`, `db`, `integrations`, `tasks`).
- No heavy business logic in route handlers.
- Typed schemas and test coverage for current endpoints.
- Observability baseline (request id, metrics, structured logging hooks).

### Partially aligned (scaffold only)
- Policy / Privacy / Education / Observability modules are currently minimal and require deeper domain logic.
- Agentic, reputation, horizon and sovereignty graph areas are not yet production-complete.
- Explainability and evidence graph are not fully represented end-to-end.

### Not yet complete vs. master prompt
- Full domain model coverage listed in the master prompt (e.g. policy execution artifacts, rich sovereignty graph, credibility intelligence) is incomplete.
- Multi-horizon intelligence and policy-as-code runtime are still roadmap items.

## 3) Reproducibility and prod hardening status

Completed in this update:
- Alembic now resolves DB URL deterministically from `DATABASE_URL` or `alembic.ini`.
- Added reproducibility check script (`scripts/check_alembic_reproducibility.sh`) and Make target `alembic-repro`.
- Added production guardrails for weak/default JWT secrets in `ENVIRONMENT=prod|production`.
- Stabilized `.env` loading path by pinning it to repository root.

## 4) Recommended next milestone

1. Expand domain models for prompt-required entities (policy execution, evidence graph, reputation profiles).
2. Add policy-as-code evaluator with persisted execution logs and explainability payloads.
3. Implement source credibility scoring pipeline and evidence-linked signal explanations.
4. Introduce contract tests for API stability and migration smoke tests in CI.


## 5) Newly completed in this iteration
- Policy runtime persistence added with `policy_execution_logs` storage and API readout endpoint (`/api/v1/policy/executions`).
- Added schema support for `TreasuryPolicy`, `PolicyRule`, and `PolicyExecutionLog` tables as a step toward policy-as-code execution traceability.

- Source reputation profiles pipeline added (refresh + listing) as the first credibility-intelligence increment.
- Signal explainability graph baseline added (`signal_explanations`, `evidence_nodes`, `evidence_edges`) with API read endpoint.
- DB-backed policy catalog and rule-based evaluation shipped (`/api/v1/policy/catalog` + runtime applied rules).

## 6) Current delivery stage
- **Stage: Late Foundation / Early Intelligence Runtime**.
- Baseline platform primitives are in place (API + persistence + tasks + observability + tests).
- Next major step to reach full prompt coverage: deepen policy-as-code, multi-horizon scoring, and sovereignty graph workflows.

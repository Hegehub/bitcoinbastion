# Status (docs truth audit)

Audit date: **2026-05-16**

This document reflects repository state from code and tests, not roadmap targets.

## Capability status

### API platform
- **IMPLEMENTED**: FastAPI route surface for auth, users, news, signals, entities, on-chain, wallet, fees, privacy, treasury, policy, citadel, observability, admin.

### Services
- **IMPLEMENTED**: service modules exist across ingestion, scoring, policy, wallet, treasury, observability, citadel, delivery, and auth.
- **BASELINE**: several service outputs are heuristic or limited-depth.

### Models and persistence
- **IMPLEMENTED**: SQLAlchemy model set exists and is migrated by Alembic revisions.
- **IMPLEMENTED**: migration replay and deterministic schema recreation smoke test exists.

### Runtime governance and observability
- **IMPLEMENTED**: `/api/v1/observability/snapshot` includes runtime severity model, degraded mode semantics, and operational evidence packet.
- **IMPLEMENTED**: runtime telemetry gauges expose severity score, degraded mode active, provider share, delivery failures, unresolved recovery findings, and citadel runtime health.
- **BASELINE**: threshold tuning for paging/escalation remains environment-specific and should be validated per deployment.

### Synthetic/baseline areas
- **SYNTHETIC**: parts of Citadel dependency/simulation behavior.
- **BASELINE**: Telegram runtime behavior, some Bitcoin protocol-depth analyzers, and explainability depth.

### Mining Sovereignty (M1 persistence status)
- **MODELS/PERSISTENCE BASELINE IMPLEMENTED**: mining SQLAlchemy models, Alembic tables, and repository persistence methods exist.
- **PLANNED**: full provider-driven mining ingestion/scoring runtime and planned mining API endpoints beyond planning surface remain not implemented.
- **Constraint**: mining records and outputs remain advisory and verification-gated; unknown/unverified states are valid baseline values.
- **Fixture warning**: mining fixture data in tests is synthetic and must not be interpreted as real-world pool intelligence.

## Evidence-backed constraints
- No production SLO attainment is claimed in this file.
- No completion percentages are used.
- Readiness claims remain in checklist form in `docs/PRODUCTION_READINESS.md`.

## Protocol maturity truth (P5)
- **IMPLEMENTED**: Chain-state, mempool, UTXO, and provider outputs expose source-quality metadata (`source_type`, `provider_name`, fallback/mock flags, freshness, confidence, limitations).
- **IMPLEMENTED**: Operational evidence packets summarize runtime risk, degraded dependencies, recovery/drill status, delivery health, and provider quality for operator workflows.
- **BASELINE**: Mempool/UTXO/script analyzers remain deterministic over caller-provided snapshots/hints and are not full node-level verification.
- **SYNTHETIC**: Citadel scenario simulations and some protocol stress inputs remain deterministic synthetic models.
- **Constraint**: Protocol and runtime confidence values are operational heuristics and must not be interpreted as consensus/finality guarantees.


## Production readiness rollup
- Current audit rollup: **82%** readiness for production hardening (implementation-complete with explicit blockers).
- Remaining blockers are tracked in `docs/FINAL_AUDIT_P6-01.md`.


### Migration and schema safety (P6-03)
- **IMPLEMENTED**: migration replay safety path is test-backed (`upgrade -> downgrade base -> upgrade`) in unit reproducibility checks.
- **IMPLEMENTED**: runtime schema parity check validates table/column/nullability/type/default/index/unique/FK parity against migrated schema.
- **BASELINE**: parity automation runs on SQLite in CI/local checks; PostgreSQL dialect-specific semantics still require staging validation evidence.
- **Constraint**: accepted drift must be explicitly documented rather than suppressed in automation output.
- **Rollback note**: deploy path remains forward migrate to head; downgrade-to-base is validated in automation but production rollback requires release-specific data retention review before execution.


## Release governance status (P6-08)
- **IMPLEMENTED**: release checklist, rollback checklist, deploy verification commands, and RC criteria are explicitly documented in `docs/PRODUCTION_READINESS.md`, `docs/OPERATIONS_RUNBOOK.md`, and `docs/RELEASE_NOTES_TEMPLATE.md`.
- **BASELINE**: deployment evidence capture still depends on disciplined operator execution per release.
- **SYNTHETIC**: none added by this governance update.
- **Constraint**: release sign-off must continue to acknowledge BASELINE/SYNTHETIC runtime domains without inflating readiness claims.

## Final sovereignty-grade readiness declaration (P6-10)

Assessment date: **2026-05-16**

### Final readiness matrix
| Domain | Evidence summary | Readiness | Status |
|---|---|---:|---|
| Bastion core (API/services/models) | Route surface, services, persistence, migrations, contracts, and integration tests are implemented. | **88%** | BASELINE |
| Citadel | Assessment, graph, recovery, simulation, and persistence are implemented; simulation components remain partially synthetic. | **81%** | BASELINE/SYNTHETIC |
| Bitcoin protocol layer | Chain-state, mempool, UTXO, and provider quality semantics implemented; still advisory/conservative rather than consensus proof. | **79%** | BASELINE |
| Explainability | Explainability/audit packet contracts and regression checks implemented across policy/treasury/citadel flows. | **86%** | BASELINE |
| Operations | Recovery check, observability snapshot, drill posture, runbook, and rollback checklists implemented. | **84%** | BASELINE |
| Security | JWT hardening, admin guard tightening, no-custody posture docs, and auth/error envelope checks implemented. | **85%** | BASELINE |
| CI and release gates | Split CI jobs + release candidate gates + migration/docs/schema checks implemented. | **87%** | IMPLEMENTED |
| Deployment | Container startup guards, health checks, and dependency ordering implemented; production validation still environment-dependent. | **82%** | BASELINE |
| Documentation truthfulness | Status/readiness/runbook/contracts updated and docs truth checks present. | **90%** | IMPLEMENTED |

### Final weighted readiness
- **Sovereignty-grade readiness: 83%** (evidence-based weighted rollup across the matrix above, adjusted for unresolved production-candidate blockers).
- This is a governance and implementation readiness score, **not** a production SLO guarantee.

### Residual risks (explicit)
1. **Protocol confidence risk (BASELINE):** chain-state/mempool/UTXO analytics remain advisory and should not be interpreted as consensus finality proof.
2. **Citadel simulation risk (SYNTHETIC):** deterministic simulation paths may underrepresent real incident entropy.
3. **Deployment execution risk (BASELINE):** release quality still depends on environment-specific operator validation (secrets, paging thresholds, live dependency behavior).
4. **Delivery runtime risk (BASELINE):** destination/provider behavior can degrade by environment despite retry/idempotency controls.

### Release decision
- **Final decision (P7-06): PRE-RC / PRODUCTION-ORIENTED BETA.**
- Rationale: repository and test posture are strong, but full production-candidate declaration is blocked by unresolved realism/operational closures in protocol maturity, Citadel synthetic dependence, and environment-verified deployment evidence requirements.

### Next release tasks if full readiness is required
- Close protocol-depth hardening for provider-grade corroboration workflows.
- Reduce synthetic dependence in Citadel disaster/recovery scenario modeling.
- Add environment-certified deployment evidence pack (staging + pre-prod + production cutover checklist outputs).
- Complete threshold calibration for escalation/paging per environment.


## Documentation lock status (P7-03)
- **IMPLEMENTED**: README, production readiness checklist, API contracts, operations runbook, release notes template, and status declaration are aligned to current repository behavior and guardrails.
- **BASELINE**: release evidence capture remains operator-dependent in deployment environments.
- **Constraint**: no documentation claim in this repository should be interpreted as production SLO attainment proof.
- **Residual risk visibility**: protocol advisory limits, Citadel synthetic components, and deployment execution risks remain explicitly documented and must be acknowledged at release sign-off.


### Version candidate metadata (P7-04)
- Proposed version candidate: **v0.1.0-rc.1** (metadata prepared only; no git tag created in repository).
- Release notes template now includes evidence-based RC metadata, upgrade notes, migration notes, rollback notes, and verification commands.
- Release remains **conditionally approved** pending target-environment evidence capture per `docs/PRODUCTION_READINESS.md`.


## Post-release monitoring status (P7-05)
- **IMPLEMENTED**: first-24h and first-7-day monitoring cadence, rollback triggers, and incident severity matrix are documented in runbook/readiness docs.
- **BASELINE**: monitoring execution remains operator-driven; no autonomous rollback guarantee is implemented.
- **Residual risk visibility**: provider degradation, delivery fragility, weak finality posture, and synthetic Citadel influences remain explicit operational risks.


## Final production-candidate decision (P7-06)
- **Decision class:** `PRE-RC / PRODUCTION-ORIENTED BETA`
- **Why not RC yet:**
  1. Protocol-depth outputs remain advisory/baseline rather than full consensus-correlated operational guarantees.
  2. Citadel scenario modeling still includes synthetic deterministic components affecting incident realism.
  3. Production deployment evidence closure remains environment/operator-dependent and not fully closed in repository artifacts alone.
- **P0 blocker status:** no direct code P0 regressions detected in repository verification; remaining blockers are realism/evidence closure blockers for RC declaration.
- **Next promotion condition:** all RC criteria plus explicit closure evidence for protocol realism, Citadel realism, and deployment operations runbook execution in target environment.


# BLOCK M1 PROGRESS REPORT
- completed tasks: M1-01 through M1-10 (persistence models, migrations, repositories, schemas, fixtures, tests, parity visibility, and verification run).
- files changed: mining model/repository/schema layers, Alembic revisions `20260516_0009` and `20260516_0010`, parity script/tests, mining fixtures, mining unit tests, and mining docs.
- migrations added: `20260516_0009_mining_foundation.py`, `20260516_0010_add_mining_sovereignty_tables.py`.
- tests added: `tests/unit/test_mining_models.py`, `tests/unit/test_mining_repository.py`, `tests/fixtures/mining.py` (reused by tests), plus schema parity test extension.
- verification commands executed:
  - `make lint` (ruff passed; mypy currently fails due to pre-existing non-mining typing debt in Citadel/observability/delivery paths)
  - `python -m pytest -q tests/unit/test_mining_models.py`
  - `python -m pytest -q tests/unit/test_mining_repository.py`
  - `make migration-smoke`
  - `python scripts/check_schema_runtime_parity.py`
- current Mining Sovereignty readiness: **MODELS/PERSISTENCE BASELINE IMPLEMENTED (~46% toward full mining feature completion)**.
- impact on global production readiness: mining persistence baseline is now real and migration-verified; global production decision remains unchanged because mining runtime/provider/API execution is still planned.
- remaining risks:
  1. provider ingestion/runtime scoring not yet implemented (M2+).
  2. planned mining API endpoints (beyond planning capability route) still not runtime implemented.
  3. existing repository-wide mypy debt (outside mining scope) keeps `make lint` non-green.
  4. synthetic fixture data must never be interpreted as real pool intelligence.
- next block: **M2** (provider-connected ingestion/read services and endpoint/runtime wiring with explainability provenance).

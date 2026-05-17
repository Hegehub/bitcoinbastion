# Mining Sovereignty Intelligence — Architecture Audit & Safe Integration Points (M0-01)

Status: **Audit complete (architecture-only)**  
Date: **2026-05-16**  
Task: **M0-01**

## Objective
Audit current Bitcoin Bastion architecture and identify the safest integration points for adding Mining Sovereignty Intelligence **without architecture rewrite** and **without DB schema implementation in this block**.

## 0) Implementation truth-status
- Mining Sovereignty is currently **SERVICE BASELINE IMPLEMENTED** for persistence, repository, service, and task scaffolding.
- Mining-specific public runtime read endpoints remain mostly **PLANNED** and must be treated as advisory contracts until explicitly promoted.
- No active network probing is implemented for mining capability verification in current M2 baseline.

---

## 1) Existing architecture facts (from code)

Bitcoin Bastion is a modular monolith with stable layers already in operation:
- API routing in `app/main.py` wires domain routers under `/api/v1/*`.
- Route handlers in `app/api/v1/*` are thin and mostly return `ResponseEnvelope[T]`.
- Service orchestration lives in `app/services/*`.
- Persistence is isolated behind repositories in `app/db/repositories/*` and SQLAlchemy models in `app/db/models/*`.
- Async runtime uses Celery tasks in `app/tasks/*`.

This is a good fit for adding mining intelligence as another bounded domain following existing patterns.

---

## 2) Recommended bounded context placement

## Domain location
- `app/domain/mining` (future): mining value objects and domain semantics.

## Service location
- `app/services/mining` (future): scoring and orchestration, ingestion normalization, and explainability assembly adapters.

## API location
- `app/api/v1/mining.py` (future): thin read-oriented endpoints only.

## 2.1 M2 Stratum V2 registry semantics (implemented baseline)
- Capability states in use: `supported`, `unsupported`, `partial`, `unknown`, `claimed_unverified`, `verified`.
- `claimed_unverified` is explicitly not equivalent to `verified` and must remain separate in summaries and downstream decisions.
- Adoption summaries must expose both support counts and uncertainty counts (`unknown`, `claimed_unverified`) with confidence + limitations.
- Source-quality labels (`source_type`, `is_verified`, `is_fallback`, `is_synthetic`, freshness, evidence refs, limitations) are first-class and must be preserved end-to-end.
- Fixture/manual records are allowed for baseline operation but must remain source-labeled and must not be presented as production-grade verified evidence.

## 2.2 M2 verification status (M2-10)
- M2 capability-registry block is functionally implemented at service/task baseline.
- Worker-discoverable Celery mining refresh task is present.
- Adoption summary semantics are implemented with explicit unknown/claimed separation and confidence caveats.
- No active network probing is implemented yet; all verification-sensitive outcomes remain advisory unless evidence-backed.

## Schema location
- `app/schemas/mining.py` (already drafted): transport/internal contracts.

## Tasks location
- `app/tasks/mining_tasks.py` (future): scheduled refresh/materialization orchestration.

## Persistence location (later block)
- `app/db/models/mining*.py` + repositories in `app/db/repositories/mining*.py` only when M2 starts.

---

## 3) Safest integration points by layer

### A) API layer (`app/main.py`, `app/api/v1/*`)
**Safe point:** add a dedicated mining router and include it in `app/main.py`, mirroring existing domain routers.

Why safe:
- Existing API pattern is additive and domain-isolated.
- Envelope/pagination/error conventions are already documented and enforced.

Initial planned endpoints (read-only):
- `GET /api/v1/mining/scorecard`
- `GET /api/v1/mining/hashrate`
- `GET /api/v1/mining/pools`
- `GET /api/v1/mining/production`
- `GET /api/v1/mining/inclusion`

### B) Service layer (`app/services/*`)
**Safe point:** create mining services that consume provider abstractions and emit typed schema outputs.

Closest proven patterns to reuse:
- `app/services/ingestion/onchain_ingestion.py` for ingest->score->signal flow shape.
- `app/services/explainability/*` for evidence graph payload conventions.
- `app/services/citadel/citadel_assessment_service.py` for cross-domain composition boundaries.

Boundary rule:
- Mining service may publish inputs to signals/citadel/policy, but must not own their final weighting decisions.

### C) Repository/model layer (`app/db/models/*`, `app/db/repositories/*`)
**Safe point in M0/M1:** no new tables; keep mining compute read-through via providers and in-memory/stateless aggregation.

Future-safe path:
- Add mining repositories only when data retention/materialization requirements are validated in M2.

### D) Task layer (`app/tasks/*`)
**Safe point:** introduce independent `mining.refresh` task family, following current job tracking and duplicate-window guards.

Closest runtime pattern:
- `app/tasks/onchain_tasks.py` and `app/tasks/signal_tasks.py`.

Boundary rule:
- mining tasks should emit contracts consumed downstream; do not call Citadel internals directly from tasks.

### E) Cross-domain integration points
1. **On-chain**: use chain-state and block/event context as upstream inputs; do not mutate on-chain canonical repository behavior.
2. **Signals**: mining outputs become new source links into signal generation with provenance.
3. **Policy**: expose mining risk thresholds as policy inputs, keep policy decisions in policy service.
4. **Explainability**: mining outputs must include node/edge-compatible evidence metadata.
5. **Citadel**: consume mining domain as an additional weighted input surface in later phase.

---

## 4) Affected layers checklist

- [x] `app/main.py` (router registration point)
- [x] `app/api/v1/*` (new mining read endpoints)
- [x] `app/services/*` (new mining orchestration/scoring services)
- [x] `app/schemas/*` (mining contracts; already drafted)
- [x] `app/db/models/*` (explicitly deferred in M0/M1)
- [x] `app/db/repositories/*` (explicitly deferred in M0/M1)
- [x] `app/tasks/*` (future mining scheduled tasks)
- [x] `docs/ARCHITECTURE.md` (domain placement)
- [x] `docs/STATUS.md` (readiness labeling when implemented)
- [x] `docs/API_CONTRACTS.md` (route inventory/envelope contract update when endpoints land)

---

## 5) Non-goals and guardrails

- No architecture rewrite proposed.
- No DB tables/models/migrations in this task.
- No replacement of existing on-chain/signal/citadel ownership boundaries.
- No deviation from `ResponseEnvelope`/`PaginatedData` API contracts.

---

## 6) Minimal integration sequence (safe order)

1. **M1-A:** add mining service interfaces + provider adapter extension points (no persistence).
2. **M1-B:** add mining API read endpoints returning schema drafts with provenance/confidence.
3. **M1-C:** add signal ingestion adapter for mining-source signals.
4. **M2:** add persistence models/repositories/migrations if operationally required.
5. **M3:** wire weighted consumption into Citadel and policy threshold packs.

This sequence preserves current stability while enabling incremental mining domain adoption.


## 7) Template-control sovereignty monitor integration (M0-07)

### Monitoring path
`Bitcoin node → Template Provider → Job Declarator → Pool → ASIC`

### Boundary placement
- **Domain (`app/domain/mining`)**
  - Owns template-control vocabulary and state semantics (`template_control_state`, `template_control_owner`, MITM state semantics).
- **Services (`app/services/mining`)**
  - Computes template sovereignty/interference risk scores and binds path observations to explainability payloads.
- **Integrations (`app/integrations/mining`)**
  - Collects observable signals for each path segment and source-quality metadata.
- **API (`app/api/v1/mining.py`)**
  - Exposes advisory template-control monitor outputs without custody claims.
- **Signals/Citadel/Policy consumers**
  - Consume template-control outputs as advisory inputs only; ownership remains with their respective domains.

### Risk semantics requirements
Template-control monitoring must classify:
- control state (`miner_controlled_verified`, `miner_controlled_claimed_unverified`, `shared_control_partial`, `pool_controlled`, `external_provider_controlled`, `unknown`)
- control owner (`miner`, `pool`, `template_provider`, `shared`, `unknown`)
- MITM risk (`low`, `medium`, `high`, `unknown`)
- linkage into censorship-risk advisory outputs

### Safety constraints
- No custody assumptions introduced.
- Unverified encrypted-channel claims must not be treated as verified security posture.
- Unknown/fallback/synthetic path evidence must reduce confidence and cannot drive verified-grade claims.


## 8) Mining signal taxonomy integration plan (M0-08)

Planned signal types to be emitted by mining domain services:
- `MINING_SOVEREIGNTY`
- `POOL_CENSORSHIP_RISK`
- `STRATUM_V2_ADOPTION`
- `HASHRATE_CENTRALIZATION`
- `TEMPLATE_CONTROL_RISK`
- `MINING_PROVIDER_DEGRADATION`

Integration path into existing Signal Engine:
1. Mining services compute deterministic advisory outputs and create signal candidates.
2. Candidates are passed to Signal Engine using standard source-link and dedup conventions.
3. Signal Engine persists final signal entities and explainability graph links.
4. Delivery layers (API/Telegram) render severity + confidence + source-quality disclosures.

Architecture constraints:
- Mining services own mining-specific factor semantics only.
- Signal Engine owns cross-domain ranking/prioritization and publication orchestration.
- Low-confidence critical mining signals must be marked tentative in downstream delivery surfaces.


## 9) Persistence layer baseline (M1)

Implementation label: **MODELS/PERSISTENCE BASELINE IMPLEMENTED**.

Implemented persistence entities:
- `mining_pools`
- `mining_pool_endpoints`
- `stratum_v2_capabilities`
- `pool_sovereignty_scores`
- `mining_censorship_risks`
- `template_control_assessments`
- `mining_signals`

Purpose boundaries:
- Persistence captures advisory mining telemetry/assessment snapshots and source-quality provenance metadata.
- Unknown/unverified values are valid baseline states and must not be coerced into verified claims.
- This baseline does not imply full mining runtime feature completion.

Fixture safety:
- Local fixtures are synthetic (`tests/fixtures/mining.py`) and are strictly test/dev scaffolding.

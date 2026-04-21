# Bitcoin Bastion — Truth Audit Status (Task ENV-01)

Audit date: **2026-04-21**

This status document is evidence-based from repository code/docs at audit time.

---

## Step 1 — Fresh repository audit

### Bastion core
- **API platform:** **IMPLEMENTED**
- **Domain execution depth:** **BASELINE**
- **Reasoning:** FastAPI routing/middleware/metrics/auth/admin/observability are wired and operational at baseline depth; some domain features remain partial.

### Citadel
- **API + persistence lifecycle:** **IMPLEMENTED**
- **Scoring/graph/simulation realism:** **SYNTHETIC**
- **Reasoning:** Endpoint surface and assessment persistence exist; several outputs are deterministic heuristic placeholders.

### Bitcoin protocol-aware layers
- **UTXO/mempool/script/descriptor services:** **BASELINE**
- **Chain-state/finality/reorg maturity:** **BASELINE**
- **Reasoning:** analyzers and route exposure exist; calibration/edge-case depth remains incomplete.

### Migrations/schema truth
- **Table coverage:** **IMPLEMENTED**
- **Reasoning:** SQLAlchemy model tables and Alembic-created tables match (27/27, no missing/extra).

### Runtime truth snapshot
- **Signal pipeline:** **BASELINE** (implemented scoring paths from news/on-chain with explainability payloads).
- **Telegram runtime:** **BASELINE** (implemented client/retries/publish flow, runtime depends on token/destination env).
- **Observability/admin runtime surfaces:** **IMPLEMENTED** for endpoint exposure, **BASELINE** for production-depth operational semantics.

---

## Step 2 — Documentation drift report

### Outdated / contradicted docs
1. `README.md` previously stated key protocol-aware services as missing while services exist (UTXO/mempool/script/descriptor).
2. `README.md` previously duplicated the **Core documentation** section multiple times.
3. `docs/API_CONTRACTS.md` previously omitted implemented endpoints:
   - `GET /api/v1/onchain/state`
   - `GET /api/v1/entities/watchlist`
   - `GET /api/v1/policy/executions/summary`
   - `POST /api/v1/wallet/profiles/{wallet_profile_id}/health`
   - `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports`
4. `docs/API_CONTRACTS.md` previously did not explicitly document non-envelope route exceptions (health/auth direct models).
5. `docs/DOMAIN_MODELS.md` previously omitted `CitadelAssessment`.

### Missing docs files
- None identified for core surfaces requested in ENV-01.

---

## Step 3 — Progress baseline (honest percentages)

These represent production-readiness toward sovereign-grade goals, not mere file presence.

- **Bastion core:** **84%**
- **Citadel:** **57%**
- **Bitcoin protocol maturity:** **62%**
- **Explainability E2E:** **63%**
- **Operations hardening:** **66%**
- **Overall finalization:** **66%**

---

## Step 4 — Safe phased execution plan

### Phase 1 — Truth and drift fixes
- Keep README/API/domain docs synchronized with implemented routes/models/services.
- Maintain evidence-based status language; avoid synthetic-overclaiming.
- Add automated route-vs-contract and model-vs-doc drift checks in CI.

### Phase 2 — Runtime hardening
- Harden Telegram and delivery workflows with clearer failure visibility and retry observability.
- Expand admin/observability semantics for production incident triage.
- Validate dependency readiness in deployment runbooks and checks.

### Phase 3 — Protocol depth
- Improve mempool/fee/UTXO calibration and edge-case handling.
- Deepen chain-state reorg/finality modeling with higher-fidelity provider data.

### Phase 4 — Citadel realism
- Replace synthetic scoring constants with evidence-backed weighted inputs.
- Expand sovereignty dependency graph realism and scenario persistence.
- Tighten cross-domain explainability linkage.

### Phase 5 — Final production readiness
- Close-loop SLO/runbook drills.
- Add regression suites for migration/schema drift and explainability guarantees.
- Gate release promotion on objective readiness checks.

---

## Step 5 — Highest-risk truth issues addressed first

1. **Migration/model truthfulness re-verified** (27/27 table coverage).
2. **README correction + duplication cleanup** completed.
3. **API/docs mismatch correction** completed.
4. **Domain model docs correction** completed.

---

## Verification notes

- Alembic remains the schema-evolution source of truth; deployment should not rely on `create_all()`.
- Current schema audit is table-level; detailed default/constraint parity should remain a tracked follow-up.

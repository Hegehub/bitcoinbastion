# Bitcoin Bastion — Truth Audit Status (Task ENV-01)

Audit date: **2026-04-21**

This status file is intentionally evidence-driven from the current repository state under:
- docs (`README.md`, `docs/*.md`)
- runtime/API (`app/main.py`, `app/api/v1/*`)
- models/migrations (`app/db/models/*`, `app/db/migrations/versions/*`)
- protocol/citadel services (`app/services/citadel/*`, `app/services/utxo/*`, `app/services/mempool/*`, `app/services/script/*`)

---

## 1) Layer classification (IMPLEMENTED / BASELINE / SYNTHETIC / MISSING / BROKEN)

| Layer | Classification | Why |
|---|---|---|
| Bastion API/platform layer | **IMPLEMENTED** | Main app wiring, middleware, metrics attachment, and route modules are present and active. |
| Bastion domain/API coverage depth | **BASELINE** | Core endpoints exist, but docs contract coverage is incomplete and several surfaces are lightly modeled. |
| Citadel endpoints + persistence lifecycle | **IMPLEMENTED** | Assessment endpoints, caching/persistence path (`citadel_assessments`) and read/write flow are in place. |
| Citadel scoring semantics | **SYNTHETIC** | Scoring relies on heuristics/constants and owner-id-dependent branches rather than production evidence pipelines. |
| Citadel dependency/simulation realism | **SYNTHETIC** | Graph and simulation services return deterministic demo-style structures/rules. |
| Bitcoin protocol service layer (UTXO/mempool/script) | **BASELINE** | Functional analyzers and schemas exist, but they are heuristic/snapshot driven and not full node-state engines. |
| Migration ↔ model table coverage | **IMPLEMENTED** | 27 model tables and 27 Alembic-created tables align; no orphan or missing tables found. |
| Reorg/finality/chain-state claims | **BASELINE** | Chain-state endpoint/service exists, but includes fallback defaults and optional provider probe behavior. |

---

## 2) Doc ↔ code mismatches (current)

### A) API contract drift

`docs/API_CONTRACTS.md` omits currently implemented endpoints:
- `GET /api/v1/onchain/state`
- `GET /api/v1/entities/watchlist`
- `GET /api/v1/policy/executions/summary`
- `POST /api/v1/wallet/profiles/{wallet_profile_id}/health`
- `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports`

### B) Response envelope overstatement

`docs/API_CONTRACTS.md` says “Most endpoints return ResponseEnvelope[T]”, but specific health/auth routes are not wrapped and return direct models:
- `GET /api/v1/health`, `/live`, `/ready` return `HealthOut`
- `POST /api/v1/auth/register` returns `UserOut`
- `POST /api/v1/auth/login` returns `TokenResponse`

This is acceptable as an exception pattern, but should be explicitly documented.

### C) Domain model documentation drift

`docs/DOMAIN_MODELS.md` does not list `CitadelAssessment`, even though it is part of `app/db/models/__init__.py` and has a dedicated migration lineage.

### D) README optimism vs runtime reality

`README.md` still presents broad capability framing (“interprets Bitcoin reality”, sovereignty survivability, etc.). Current Citadel/protocol implementations are partly synthetic/baseline and should be described as such to avoid overclaiming.

---

## 3) Migration ↔ model audit

Result from direct repository audit:
- Model tables discovered from SQLAlchemy metadata: **27**
- `op.create_table(...)` occurrences in Alembic revisions: **27 unique**
- Model tables missing in migrations: **0**
- Migration-created tables missing in models: **0**

Conclusion:
- **Table-level migration/model coverage is IMPLEMENTED.**
- This audit does **not** claim perfect column/default/constraint parity beyond table presence.

---

## 4) Honest progress percentages (evidence-based)

These percentages reflect **production-readiness toward stated docs ambitions**, not mere file existence.

- **Bastion API/platform core:** **86%**
  - Strong routing/foundation present; some contract documentation drift remains.
- **Bitcoin protocol intelligence layer (UTXO/mempool/script + chain-state):** **61%**
  - Baseline analyzers implemented; depth and real-world calibration are incomplete.
- **Citadel sovereignty layer:** **58%**
  - Endpoint surface and persistence exist; scoring/graph/simulation logic is still significantly synthetic.
- **Model/migration governance:** **92%**
  - Table coverage is complete; deeper DDL/operational drift checks still separate.
- **Overall (repo truth vs target narrative):** **67%**

---

## 5) Priority cleanup list

1. Update `docs/API_CONTRACTS.md` to include all currently exposed endpoints and explicit non-envelope exceptions.
2. Update `docs/DOMAIN_MODELS.md` to include `CitadelAssessment`.
3. Add explicit “synthetic/baseline” labels in `README.md` and architecture docs for Citadel/protocol components.
4. Add automated contract extraction or route-vs-doc validation in CI to prevent drift recurrence.

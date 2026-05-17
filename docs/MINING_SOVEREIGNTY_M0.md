# Mining Sovereignty Intelligence — Block M0 Foundation

Status: **Draft foundation (M0)**  
Date: **2026-05-16**  
Scope: architecture, boundaries, schema drafts, and integration plan.

## 1) Domain intent
Mining Sovereignty Intelligence extends Bitcoin Bastion with miner- and network-production-centric intelligence so operators can reason about censorship pressure, concentration risk, transaction inclusion dynamics, and fee-market pressure with explainable evidence.

This block deliberately avoids persistence migration work and DB tables.

## 2) Bounded context
### In scope (M0)
- Domain model semantics (language + contracts)
- Service/module boundaries
- API/schema contract drafts
- Integration points with existing on-chain, signal, policy, explainability, and Citadel flows
- Delivery of a staged implementation plan

### Out of scope (M0)
- Alembic migrations
- SQLAlchemy model/table creation
- Historical backfill jobs
- Provider vendor lock-in decisions

## 3) Proposed architecture placement
New module placement in modular monolith:
- `app/domain/mining`: domain concepts and stateless value objects
- `app/services/mining`: orchestration and scoring services
- `app/integrations/bitcoin/*`: provider adapters reused/extended for mining telemetry
- `app/tasks/mining_tasks.py`: async refresh/materialization workflows (future block)
- `app/schemas/mining.py`: API and internal exchange contracts (drafted in M0)

Boundary rules:
1. Mining services consume provider/integration abstractions, not concrete clients.
2. API handlers remain thin and delegate to mining services.
3. Signal engine ingests mining outputs through explicit contracts only.
4. Explainability references mining evidence using common evidence graph conventions.

## 4) Draft subdomains and capabilities
1. **Hashrate & Difficulty Intelligence**
   - hashrate trend regime detection
   - difficulty adjustment pressure
2. **Pool Concentration & Governance Risk**
   - top-pool dominance metrics
   - concentration shocks and threshold alerts
3. **Block Production Integrity**
   - stale/orphan pressure indicators
   - empty-block or anomalous production patterns
4. **Inclusion & Censorship Signals**
   - transaction inclusion lag profiles
   - policy-filter footprint heuristics (where data permits)
5. **Fee-Market Coupling**
   - mining incentives vs mempool congestion coupling
   - stress-period miner behavior flags

## 5) Data contracts (M0 draft)
All schemas are intentionally persistence-agnostic. They support API payloads, task payloads, and explainability assembly.

Primary draft entities:
- `MiningWindow`
- `HashrateSnapshot`
- `PoolShareSnapshot`
- `BlockProductionSnapshot`
- `InclusionCensorshipSnapshot`
- `MiningSovereigntyScorecard`
- `MiningExplainabilityNode`

See `app/schemas/mining.py` for concrete draft fields.

## 6) Integration boundaries with existing domains
### On-chain Intelligence
- Reuse chain-state metadata and confirmation/finality context.
- Mining domain may enrich on-chain risk narratives but must not overwrite on-chain canonical facts.

### Signal Engine
- Mining scorecard publishes domain signal inputs with confidence and provenance.
- Signal composition weights remain owned by signal services (not mining domain).

### Policy Runtime
- Mining risk thresholds exposed as policy-check inputs.
- Policy decisions remain in policy runtime services.

### Citadel
- Citadel consumes mining sovereignty slices as one weighted domain in future phases.
- No synthetic fallback constants should be introduced for mining in M0.

### Explainability
- Mining outputs must provide evidence nodes/edges compatible with existing explainability contracts.

## 7) Staged implementation plan
### M0 (this block)
- Finalize architecture and schema draft contracts.
- Define service and task entrypoint boundaries.
- Document integration touchpoints and sequencing.

### M1
- Implement provider abstraction extensions for mining telemetry.
- Add read-only service computations and API endpoints (no writes).
- Add contract/unit tests for schema and scoring math.

### M2
- Add persistence models + migrations.
- Introduce scheduled ingestion/materialization tasks.
- Wire explainability graph persistence.

### M3
- Integrate into Signal/Citadel weighted scoring.
- Add policy threshold packs and operational alerts.
- Calibrate with historical stress windows.

## 8) Risks and controls
- **Provider heterogeneity risk** → normalize through adapter contracts and provenance tags.
- **False censorship positives** → require confidence scoring + explicit uncertainty fields.
- **Cross-domain coupling creep** → enforce service ownership and unidirectional dependencies.
- **Explainability gaps** → block release if evidence lineage is absent for high-impact flags.

## 9) Definition of done (M0)
- Mining domain documented with clear boundaries.
- Draft schemas committed and importable.
- Architecture docs include mining as a first-class intelligence domain.
- Integration plan explicitly staged with no DB work in M0.

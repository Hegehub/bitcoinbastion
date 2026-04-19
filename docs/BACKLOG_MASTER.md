# BACKLOG MASTER

This backlog reflects the current code reality and the remaining work needed to reach sovereignty-grade production finalization.

## Status framing
The repository already includes:
- Bastion API platform
- wallet / privacy / treasury / policy domains
- explainability models
- Citadel API and assessment persistence
- protocol-aware services:
  - UTXO
  - mempool
  - script
  - descriptor awareness

But the system is not yet fully finalized.

## Phase 1 — Truth and integrity
### BKL-01
Fix migration truthfulness and align Alembic history with the real model graph.

### BKL-02
Perform full schema truth audit and document model-table-migration coverage.

### BKL-03
Correct docs/STATUS and production-readiness language where it overstates completion.

## Phase 2 — Runtime hardening
### BKL-04
Finalize signal runtime orchestration and eliminate synthetic/empty generation paths.

### BKL-05
Finalize Telegram runtime and delivery orchestration.

### BKL-06
Strengthen admin/operator recovery and job retry workflows.

## Phase 3 — Bitcoin protocol depth
### BKL-07
Deepen UTXO integration into wallet and Citadel outputs.

### BKL-08
Deepen mempool/fee-market integration into treasury and Citadel scenarios.

### BKL-09
Finalize chain-state / finality / reorg-risk service.

### BKL-10
Strengthen provider realism and fallback behavior.

### BKL-11
Deepen script and descriptor awareness integration into recovery readiness.

## Phase 4 — Citadel realism
### BKL-12
Replace synthetic Citadel score inputs with real domain-linked signals.

### BKL-13
Upgrade sovereignty graph realism and dependency topology depth.

### BKL-14
Upgrade disaster simulation realism and scenario coverage.

### BKL-15
Deepen recovery artifact verification and inheritance readiness semantics.

### BKL-16
Strengthen repair plan prioritization from real risk and resilience deltas.

## Phase 5 — Explainability and governance
### BKL-17
Close cross-domain explainability traceability for high-impact decisions.

### BKL-18
Finalize policy lifecycle governance and risk-aware simulation/compare flows.

## Phase 6 — Operations finalization
### BKL-19
Close automated drills and recovery SLO loop.

### BKL-20
Run final truth-based production readiness pass.

## Progress rule
Every task update must include:
- overall % complete
- current phase %
- completed tasks
- remaining tasks
- newly discovered risks
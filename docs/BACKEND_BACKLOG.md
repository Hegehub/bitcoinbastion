# BACKEND BACKLOG

## Scope
This file tracks backend-only work still needed to reach production-grade finalization.

## P0
### BE-01
Fix migration/model drift.
Outcome:
- Alembic reflects the real schema
- no hidden reliance on test-only schema creation

### BE-02
Finalize signal runtime.
Outcome:
- task-driven signal generation is real
- persistence and explanation are consistent

### BE-03
Finalize Telegram delivery path.
Outcome:
- real bot runtime
- retries
- delivery logs
- duplicate suppression

## P1
### BE-04
Implement and wire chain-state/finality/reorg service.
Outcome:
- production-grade confirmation semantics
- risk-aware downstream logic

### BE-05
Strengthen provider fallback and provider health propagation.
Outcome:
- on-chain and protocol-aware services less mock-dependent

### BE-06
Deepen UTXO/mempool integration with wallet, fees, treasury, Citadel.
Outcome:
- protocol-aware decisions are not isolated helpers

### BE-07
Deepen descriptor/recovery semantics.
Outcome:
- recovery readiness uses real metadata assumptions

## P2
### BE-08
Replace synthetic Citadel score constants with real domain-linked inputs.

### BE-09
Upgrade sovereignty graph topology.

### BE-10
Upgrade disaster simulation determinism and realism.

### BE-11
Strengthen explainability graph usage across signals, policy, and Citadel.

### BE-12
Close automated recovery drills + SLO loop.

### BE-13
Final production readiness audit.

## Definition of done
Backend is only considered finalized when:
- schema is truthful
- protocol layers materially affect decisions
- Citadel outputs are not materially synthetic
- explainability is cross-domain usable
- ops and recovery loops are observable and testable
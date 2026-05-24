# Bastion Trace

## Overview
Bastion Trace is a **Bitcoin-first, watch-only, no-custody module** inside Bitcoin Bastion for advisory analysis of public Bitcoin addresses.

Bastion Trace is **not** the whole platform. It contributes risk/privacy/context signals and evidence artifacts to other modules (Citadel, Policy, Treasury, Register) through explicit bridge outputs.

## What Bastion Trace is
- Advisory-only address analysis.
- Deterministic baseline scoring and confidence outputs.
- Evidence-oriented reporting (report/evidence/receipt/proof packet/replay).
- Privacy baseline heuristics (UTXO hygiene, dust radar, address reuse, consolidation risk, toxic change).
- Counterparty/payment-context advisory outputs.
- Capability-tier abstractions (Lite/Pro/Business/Enterprise) as backend baselines.

## What Bastion Trace is not
- Not custody.
- Not a wallet.
- Not transaction signing.
- Not transaction broadcast.
- Not legal/compliance verdicting.
- Not Bitcoin consensus proof.
- Not production-calibrated chain analytics.

## Safety model
- Public-address only inputs.
- Sensitive wallet material is rejected (seed phrases/private keys/wallet-secret patterns).
- Operator-controlled advisory outputs with explicit limitations.
- Privacy exposure is not equivalent to illicit-risk evidence.

## How it fits in Bitcoin Bastion
- Citadel consumes Trace as a separate advisory contribution.
- Policy Bridge exposes policy facts/recommendations but does not execute payments.
- Treasury Bridge provides destination advisory only and does not sign/broadcast transactions.
- Register Bridge provides merchant advisory only; no auto-reject/auto-accept enforcement by default.

## Current implementation status
**Bastion Trace: BACKEND BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED**

Substatus:
- Core Trace: BASELINE
- Scoring/Trace DNA/Confidence: BASELINE
- Evidence/Receipt/Replay/Proof Packet: BASELINE
- Origin/Source Registry/Freshness/Provider Disagreement: BASELINE
- Privacy Shield + UTXO heuristics: BASELINE
- Counterparty + Payment Context + Safe-to-Send: BASELINE
- Lite Tier: BASELINE
- Pro Tier: BASELINE
- Business Tier: BASELINE
- Enterprise Tier: BASELINE/PLACEHOLDER
- Integrations (Citadel/Policy/Treasury/Register): BASELINE
- Observability + Runtime Events: BASELINE
- Website UI: NOT IMPLEMENTED

## Limitations summary
- Deterministic baseline weights; no production calibration evidence.
- Source adapters and signal quality are still baseline.
- Heuristic privacy/UTXO modules are source-limited.
- Enterprise controls depend on external auth/SSO/SIEM infrastructure to become production-enforced.

## Roadmap direction
- Production calibration and validation evidence.
- Source quality hardening and stronger chain-state corroboration.
- Stronger auth/rate-limiting/policy enforcement integration.
- UI and operator workflow hardening.


Bastion Trace backend is baseline hardened but not production-calibrated. Replay determinism depends on preserved evidence snapshots. Proof packets are evidence bundles, not legal certificates. Sensitive wallet material is rejected and not stored. Production deployment still requires auth/rate limiting/observability validation.

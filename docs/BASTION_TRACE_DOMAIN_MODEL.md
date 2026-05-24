# Bastion Trace Domain Model

Purpose: map implemented Bastion Trace persistence and service artifacts to operator-facing concepts.

## Core persisted models
- `TraceReport`: top-level address analysis output with score/band/confidence, reason codes, limitations, guidance.
- `TraceEvidence`: report evidence entries with source metadata.
- `TraceSource` / `TraceSourceSnapshot`: source registry and quality/freshness snapshots.
- `TraceWatchlistEntry`: watch-only address watchlist.

## Extended persisted baseline models
- Batch/business: `TraceBatch`, `TraceBatchItem`, `TraceBusinessPolicyProfile`, `TraceReviewItem`, `TraceOperatorNote`, `TraceBusinessProofPacket`, `TraceBusinessExport`, `TraceBusinessEvent`.
- Enterprise: legal hold/audit/SIEM/retention/evidence-governance/enterprise proof packet tables.
- Runtime observability: `TraceRuntimeEvent`, `TraceAlert`.

## Service-level domain artifacts (serialized JSON fields / response DTOs)
- Trace DNA and score breakdown outputs.
- Trace receipt/proof packet-style advisory artifacts.
- Origin passport and provider disagreement results.
- Privacy shield reports (UTXO hygiene, dust radar, address reuse, consolidation risk, toxic change).
- Counterparty lens and payment context outputs.
- Lite report abstraction.
- Pro/business/enterprise capability profiles.
- Integration bridge objects (Citadel/Policy/Treasury/Register/Evidence/Operations).

## Safety flags and invariants
- Advisory-only outputs.
- Not legal verdict.
- Not consensus proof.
- No custody.
- No seed/private key handling.
- No transaction signing/broadcasting.

## Persistence/readiness notes
- Persistence is implemented for major trace and business/enterprise artifacts.
- Many advanced constructs remain baseline/placeholder and are not production-calibrated.

# Bastion Trace RC Gap Audit

Audit date: 2026-05-23

## Implemented
- Core Trace backend module, scoring, persistence, API routes, and baseline observability.
- Privacy/Counterparty/Payment-context baseline outputs.
- Lite/Pro/Business/Enterprise capability-profile baselines.
- Integration bridge outputs (Citadel/Policy/Treasury/Register/Evidence/Operations).

## Baseline (not production-calibrated)
- Scoring weights and source-quality semantics.
- Replay/proof behavior where deterministic output depends on preserved evidence snapshots.
- Privacy/UTXO heuristics.
- Policy/business/enterprise operational recommendations.

## Placeholder
- Enterprise RBAC/SSO/SIEM enforcement without external auth/IdP/SIEM runtime integration.
- Alert delivery where environment delivery infrastructure is absent.

## Missing for production-complete RC
- External source calibration evidence.
- Production auth/rate-limiting hardening evidence for public/business endpoints.
- Production observability dashboard + alert routing validation evidence.
- UI/runtime operator workflow evidence.

## Category breakdown
- Core Trace: BASELINE IMPLEMENTED
- Replay: BASELINE (snapshot-dependent determinism)
- Proof Packets: BASELINE (evidence bundle, not legal certificate)
- Privacy: BASELINE
- Counterparty: BASELINE
- Lite: BASELINE
- Pro: BASELINE
- Business: BASELINE
- Enterprise: BASELINE/PLACEHOLDER
- Integrations: BASELINE
- Observability: BASELINE
- Telegram: BASELINE/ENVIRONMENT-DEPENDENT
- DB/Migrations: IMPLEMENTED with migration smoke checks
- Operations: BASELINE
- Docs: ALIGNED BASELINE

## Required external validation
- Staging/production migration replay and schema parity evidence.
- Public endpoint rate-limit and abuse-control validation.
- Authz enforcement validation for business/enterprise paths.
- Deployment evidence pack artifacts attached at release commit.

## Safety truth lock
- Bastion Trace backend is baseline hardened but not production-calibrated.
- Sensitive wallet material is rejected and not stored.
- No transaction signing or broadcasting.
- No legal verdicts; no Bitcoin consensus proof.

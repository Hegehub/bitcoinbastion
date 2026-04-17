# SPEC — Bitcoin Citadel (Extension to Bitcoin Bastion)

## Product intent
Bitcoin Citadel answers resilience questions for custody, privacy, recovery, and treasury survivability.

## Initial delivery scope (CIT-1)
- Citadel assessment domain model
- typed schemas for assessment payloads
- test coverage for schema + model persistence defaults

## Phase roadmap
- CIT-1 Foundations (models/schemas/repositories baseline)
- CIT-2 Structural graph (dependencies + SPOF detection)
- CIT-3 Recovery proofing
- CIT-4 Deterministic disaster simulations
- CIT-5 Inheritance + treasury + policy maturity integration
- CIT-6 API `/api/v1/citadel/*` + hardening

## Mandatory traits
- explainable outputs
- reproducible scoring
- frontend-ready payloads
- shared response envelope compatibility
- reuse existing Bastion wallet/privacy/treasury/policy/observability data

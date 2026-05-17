# Citadel Synthetic Risk Register

All baseline/synthetic Citadel outputs must carry explicit synthetic governance fields:
- synthetic_component
- synthetic_reason
- production_replacement_path
- confidence_penalty
- operator_warning
- evidence_refs
- limitations
- source_quality

Covered outputs:
- Citadel assessment
- Dependency graph
- Recovery readiness
- Disaster simulations
- Inheritance readiness
- Repair plan

Policy: synthetic/baseline logic is retained but never presented as production-grade attestation.

# Protocol Corroboration and Finality Confidence

Protocol-aware outputs are advisory operational signals, not consensus proof.

Required fields now exposed in protocol freshness metadata:
- provider_count
- corroborated_by
- conflicting_providers
- confidence_adjustment
- freshness_band
- fallback_active
- single_source_advisory
- advisory_not_consensus_proof
- operator_guidance
- limitations

Confidence hardening rules:
- fallback and stale sources reduce confidence
- single-source data is marked advisory and confidence-reduced
- provider conflicts reduce confidence
- reorg risk reasoning is exposed in explainability

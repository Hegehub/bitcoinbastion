"""Mining service-layer responsibilities.

M0-02 scope:
- Defines orchestration responsibilities for mining intelligence.
- Full scoring/ingestion logic intentionally deferred.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningServiceResponsibilities:
    """Service ownership map for mining modules."""

    responsibilities: tuple[str, ...] = (
        "normalize_provider_payloads",
        "compute_mining_scorecard",
        "assemble_explainability_payloads",
        "publish_signal_inputs",
        "expose_read_models_for_api",
    )

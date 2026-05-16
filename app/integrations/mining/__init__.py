"""Mining integration boundary.

M0-02 scope:
- Adapter contracts for external mining telemetry providers.
- Concrete clients are intentionally deferred.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningIntegrationBoundary:
    """Integration contract responsibilities for mining providers."""

    responsibilities: tuple[str, ...] = (
        "fetch_hashrate_telemetry",
        "fetch_pool_share_telemetry",
        "fetch_block_production_telemetry",
        "fetch_inclusion_delay_telemetry",
        "attach_source_provenance_metadata",
    )

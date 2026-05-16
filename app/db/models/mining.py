"""Mining persistence model planning placeholder.

M0-02 constraint:
- No table schema implementation in this block.
- This module only records intended model responsibilities.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningModelPlan:
    entities: tuple[str, ...] = (
        "mining_windows",
        "hashrate_snapshots",
        "pool_share_snapshots",
        "block_production_snapshots",
        "inclusion_censorship_snapshots",
        "mining_scorecards",
    )

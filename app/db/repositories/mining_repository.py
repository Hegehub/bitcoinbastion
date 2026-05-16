"""Mining repository planning placeholder.

M0-02 scope:
- Defines expected repository responsibilities.
- Concrete SQLAlchemy implementation deferred.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningRepositoryPlan:
    responsibilities: tuple[str, ...] = (
        "persist_mining_snapshots",
        "load_latest_scorecard",
        "query_time_window_series",
        "store_provenance_metadata",
    )

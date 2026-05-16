"""Mining task planning placeholder.

M0-02 scope:
- Defines intended scheduled tasks for mining intelligence.
- Task execution logic is intentionally deferred.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningTaskPlan:
    tasks: tuple[str, ...] = (
        "tasks.mining.refresh_telemetry",
        "tasks.mining.compute_scorecard",
        "tasks.mining.publish_signal_inputs",
    )

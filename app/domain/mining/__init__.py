"""Mining domain boundaries.

M0-02 scope:
- Hosts mining sovereignty domain vocabulary and invariants.
- No persistence or provider orchestration logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MiningDomainBoundary:
    """Declarative boundary descriptor for architecture planning."""

    context_name: str = "mining_sovereignty"
    ownership: tuple[str, ...] = (
        "hashrate_and_difficulty_semantics",
        "pool_concentration_semantics",
        "block_production_integrity_semantics",
        "inclusion_neutrality_semantics",
    )

from __future__ import annotations

from enum import Enum
from typing import Protocol

from app.services.bastion_trace.claims.domain import (
    BitcoinNetworkClaimValue,
    TraceClaim,
    TraceClaimPredicate,
)


class TraceComparisonOutcome(str, Enum):
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    NOT_COMPARABLE = "not_comparable"


class TraceClaimComparator(Protocol):
    predicate: TraceClaimPredicate

    def compare(self, claims: tuple[TraceClaim, ...]) -> TraceComparisonOutcome: ...


class BitcoinNetworkClaimComparator:
    """Compares mutually exclusive canonical Bitcoin network classifications."""

    predicate = TraceClaimPredicate.BITCOIN_NETWORK
    independent_producer_groups = frozenset(
        {"bitcoin-address-syntax-network", "bitcoin-observation-source-network"}
    )
    supported_networks = frozenset({"bitcoin-mainnet", "bitcoin-testnet"})

    def compare(self, claims: tuple[TraceClaim, ...]) -> TraceComparisonOutcome:
        if len(claims) < 2:
            return TraceComparisonOutcome.NOT_COMPARABLE
        if not self.independent_producer_groups <= {claim.producer_id for claim in claims}:
            return TraceComparisonOutcome.NOT_COMPARABLE
        values: set[str] = set()
        for claim in claims:
            if claim.predicate is not self.predicate:
                return TraceComparisonOutcome.NOT_COMPARABLE
            if not isinstance(claim.value, BitcoinNetworkClaimValue):
                return TraceComparisonOutcome.NOT_COMPARABLE
            if claim.value.network not in self.supported_networks:
                return TraceComparisonOutcome.NOT_COMPARABLE
            values.add(claim.value.network)
        if len(values) == 1:
            return TraceComparisonOutcome.AGREEMENT
        return TraceComparisonOutcome.DISAGREEMENT


COMPARATORS: dict[TraceClaimPredicate, TraceClaimComparator] = {
    TraceClaimPredicate.BITCOIN_NETWORK: BitcoinNetworkClaimComparator(),
}

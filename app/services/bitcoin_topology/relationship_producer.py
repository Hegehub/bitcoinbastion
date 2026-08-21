from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.services.bitcoin_observations.domain import (
    AddressObserved,
    BitcoinObservation,
    TransactionObserved,
)
from app.services.bitcoin_topology.domain import (
    RELATIONSHIP_VERSION,
    BitcoinTopologyDirection,
    BitcoinTopologyObjectRef,
    BitcoinTopologyObjectType,
    BitcoinTopologyProvenance,
    BitcoinTopologyRelationship,
    BitcoinTopologyRelationshipType,
    stable_relationship_id,
    stable_topology_object_id,
)

PRODUCER_NAME = "BitcoinTopologyRelationshipProducer"
BUILDER_VERSION = "bitcoin-topology-relationship-builder-v1"


@dataclass(frozen=True, slots=True)
class BitcoinTopologyValidationFailure:
    message: str
    observation_id: str = ""


class BitcoinTopologyRelationshipError(ValueError):
    def __init__(self, failures: tuple[BitcoinTopologyValidationFailure, ...]) -> None:
        self.failures = failures
        detail = "; ".join(failure.message for failure in failures)
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class BitcoinTopologyRelationshipBatch:
    relationships: tuple[BitcoinTopologyRelationship, ...]


class BitcoinTopologyRelationshipProducer:
    """Canonical producer for relationships reproducible from Bitcoin observations."""

    def produce(
        self, observations: tuple[BitcoinObservation, ...]
    ) -> BitcoinTopologyRelationshipBatch:
        self._validate_observations(observations)
        transactions = {
            observation.txid: observation
            for observation in observations
            if isinstance(observation, TransactionObserved) and observation.txid
        }
        relationships: dict[str, BitcoinTopologyRelationship] = {}
        for observation in observations:
            if not isinstance(observation, AddressObserved):
                continue
            if not observation.txid or observation.txid not in transactions:
                continue
            tx_observation = transactions[observation.txid]
            relationship = self._address_participates_in_transaction(
                address_observation=observation,
                transaction_observation=tx_observation,
            )
            relationships[relationship.id] = relationship
        return BitcoinTopologyRelationshipBatch(
            relationships=tuple(relationships[key] for key in sorted(relationships))
        )

    def reject_unsupported_relationship(
        self, relationship_type: str
    ) -> None:
        if relationship_type != BitcoinTopologyRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION.value:
            raise BitcoinTopologyRelationshipError(
                (
                    BitcoinTopologyValidationFailure(
                        f"unsupported relationship type: {relationship_type}"
                    ),
                )
            )

    def _address_participates_in_transaction(
        self,
        *,
        address_observation: AddressObserved,
        transaction_observation: TransactionObserved,
    ) -> BitcoinTopologyRelationship:
        source = BitcoinTopologyObjectRef(
            object_type=BitcoinTopologyObjectType.ADDRESS,
            object_id=stable_topology_object_id(
                BitcoinTopologyObjectType.ADDRESS,
                address_observation.address,
                network=address_observation.provenance.source.network,
            ),
            value=address_observation.address,
            network=address_observation.provenance.source.network,
        )
        target = BitcoinTopologyObjectRef(
            object_type=BitcoinTopologyObjectType.TRANSACTION,
            object_id=stable_topology_object_id(
                BitcoinTopologyObjectType.TRANSACTION,
                transaction_observation.txid or "",
                network=transaction_observation.provenance.source.network,
            ),
            value=transaction_observation.txid or "",
            network=transaction_observation.provenance.source.network,
        )
        observation_ids = tuple(
            sorted((address_observation.id, transaction_observation.id))
        )
        limitations = tuple(
            sorted(
                set(address_observation.provenance.limitations)
                | set(transaction_observation.provenance.limitations)
                | {"no_ownership_inference", "no_counterparty_inference"}
            )
        )
        provenance = BitcoinTopologyProvenance(
            producer=PRODUCER_NAME,
            builder_version=BUILDER_VERSION,
            originating_observation_ids=observation_ids,
            source=address_observation.provenance.source,
            limitations=limitations,
        )
        return BitcoinTopologyRelationship(
            id=stable_relationship_id(
                BitcoinTopologyRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION,
                source,
                target,
                observation_ids,
            ),
            relationship_version=RELATIONSHIP_VERSION,
            relationship_type=BitcoinTopologyRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION,
            direction=BitcoinTopologyDirection.DIRECTED,
            source=source,
            target=target,
            producer=PRODUCER_NAME,
            created_at=self._created_at(address_observation, transaction_observation),
            provenance=provenance,
            limitations=limitations,
        )

    def _validate_observations(self, observations: tuple[BitcoinObservation, ...]) -> None:
        failures: list[BitcoinTopologyValidationFailure] = []
        seen: set[str] = set()
        for observation in observations:
            if observation.id in seen:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        "duplicate observation identity", observation.id
                    )
                )
            seen.add(observation.id)
            if not observation.provenance.producer:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        "observation provenance producer is missing", observation.id
                    )
                )
            if not observation.provenance.source.source_name:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        "observation provenance source is missing", observation.id
                    )
                )
        if failures:
            raise BitcoinTopologyRelationshipError(tuple(failures))

    @staticmethod
    def _created_at(
        address_observation: AddressObserved, transaction_observation: TransactionObserved
    ) -> datetime:
        values = [address_observation.observed_at, transaction_observation.observed_at]
        values.sort()
        return values[0] if values else datetime.now(UTC)

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest

from app.db.models.onchain import OnchainEvent
from app.services.bitcoin_observations.domain import BitcoinObservationProvenance
from app.services.bitcoin_observations.producer import BitcoinObservationProducer
from app.services.bitcoin_topology.domain import (
    RELATIONSHIP_VERSION,
    BitcoinTopologyDirection,
    BitcoinTopologyObjectType,
    BitcoinTopologyRelationshipType,
)
from app.services.bitcoin_topology.relationship_producer import (
    BUILDER_VERSION,
    BitcoinTopologyRelationshipError,
    BitcoinTopologyRelationshipProducer,
)


def event() -> OnchainEvent:
    return OnchainEvent(
        event_type="mempool_recent_tx",
        txid="ABCDEF1234",
        address="bc1qexample",
        value_sats=2500,
        fee_sats=125,
        block_height=900000,
        observed_at=datetime(2026, 8, 14, tzinfo=UTC),
        provider="esplora",
        raw_payload_json='{"provider":"esplora","source_type":"provider"}',
        confidence_score=0.91,
    )


def observations():
    return BitcoinObservationProducer().from_onchain_event(event()).observations


def relationships():
    return BitcoinTopologyRelationshipProducer().produce(observations()).relationships


def test_stable_relationship_identity_and_determinism() -> None:
    first = relationships()
    second = relationships()
    assert [item.id for item in first] == [item.id for item in second]
    assert len(first) == 1


def test_duplicate_prevention_rejects_duplicate_observation_id() -> None:
    obs = observations()
    with pytest.raises(BitcoinTopologyRelationshipError):
        BitcoinTopologyRelationshipProducer().produce((obs[0], obs[0]))


def test_relationship_direction_and_type_are_blockchain_semantic() -> None:
    relationship = relationships()[0]
    assert relationship.relationship_type is BitcoinTopologyRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION
    assert relationship.direction is BitcoinTopologyDirection.DIRECTED
    assert relationship.source.object_type is BitcoinTopologyObjectType.ADDRESS
    assert relationship.target.object_type is BitcoinTopologyObjectType.TRANSACTION


def test_unsupported_relationship_rejection() -> None:
    with pytest.raises(BitcoinTopologyRelationshipError):
        BitcoinTopologyRelationshipProducer().reject_unsupported_relationship("same_owner")


def test_provenance_preservation() -> None:
    relationship = relationships()[0]
    assert relationship.producer == "BitcoinTopologyRelationshipProducer"
    assert relationship.relationship_version == RELATIONSHIP_VERSION
    assert relationship.provenance.builder_version == BUILDER_VERSION
    assert len(relationship.provenance.originating_observation_ids) == 2
    assert relationship.provenance.source.source_name == "esplora"
    assert "no_ownership_inference" in relationship.limitations


def test_validation_rejects_missing_provenance_source() -> None:
    obs = observations()
    broken = replace(
        obs[0],
        provenance=BitcoinObservationProvenance(
            producer=obs[0].provenance.producer,
            source=replace(obs[0].provenance.source, source_name=""),
            limitations=obs[0].provenance.limitations,
        ),
    )
    with pytest.raises(BitcoinTopologyRelationshipError):
        BitcoinTopologyRelationshipProducer().produce((broken,))


def test_relationship_is_immutable() -> None:
    relationship = relationships()[0]
    with pytest.raises(FrozenInstanceError):
        relationship.producer = "other"  # type: ignore[misc]


def test_no_relationship_without_transaction_observation() -> None:
    obs = tuple(item for item in observations() if item.txid is None or item.observation_type.value != "transaction_observed")
    assert BitcoinTopologyRelationshipProducer().produce(obs).relationships == ()

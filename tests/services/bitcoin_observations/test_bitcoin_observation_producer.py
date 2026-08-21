from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.onchain import OnchainEvent
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import ChainEvent
from app.services.bitcoin_observations.domain import (
    OBSERVATION_VERSION,
    BitcoinObservationType,
)
from app.services.bitcoin_observations.producer import BitcoinObservationProducer


def event(txid: str = "ABCDEF1234", address: str = " bc1qexample ") -> OnchainEvent:
    return OnchainEvent(
        event_type="mempool_recent_tx",
        txid=txid,
        address=address,
        value_sats=2500,
        fee_sats=125,
        block_height=900000,
        observed_at=datetime(2026, 8, 14, tzinfo=UTC),
        provider="esplora",
        raw_payload_json=(
            '{"provider":"esplora","source_type":"provider",'
            '"limitations":"Mempool-derived event."}'
        ),
        confidence_score=0.91,
    )


def test_stable_observation_identity_and_producer_determinism() -> None:
    producer = BitcoinObservationProducer()
    first = producer.from_onchain_event(event())
    second = producer.from_onchain_event(event())
    assert [item.id for item in first.observations] == [item.id for item in second.observations]
    assert [item.observation_type for item in first.observations] == [
        item.observation_type for item in second.observations
    ]


def test_immutability() -> None:
    observation = BitcoinObservationProducer().from_onchain_event(event()).observations[0]
    with pytest.raises(FrozenInstanceError):
        observation.producer = "other"  # type: ignore[misc]


def test_canonical_normalization_and_types() -> None:
    observations = BitcoinObservationProducer().from_onchain_event(event()).observations
    by_type = {item.observation_type: item for item in observations}
    assert by_type[BitcoinObservationType.TRANSACTION_OBSERVED].txid == "abcdef1234"
    assert by_type[BitcoinObservationType.ADDRESS_OBSERVED].address == "bc1qexample"  # type: ignore[attr-defined]
    assert by_type[BitcoinObservationType.FEE_OBSERVED].txid == "abcdef1234"
    assert by_type[BitcoinObservationType.CONFIRMATION_OBSERVED].block_height == 900000


def test_duplicate_prevention_by_stable_identity() -> None:
    observations = BitcoinObservationProducer().from_onchain_event(event()).observations
    assert len({item.id for item in observations}) == len(observations)


def test_provenance_preservation() -> None:
    observation = BitcoinObservationProducer().from_onchain_event(event()).observations[0]
    assert observation.provenance.producer == "BitcoinObservationProducer"
    assert observation.provenance.source.source_name == "esplora"
    assert observation.provenance.source.indexer_origin == "esplora"
    assert "no_relationships" in observation.provenance.limitations


def test_version_semantics() -> None:
    observation = BitcoinObservationProducer().from_onchain_event(event()).observations[0]
    assert observation.observation_version == OBSERVATION_VERSION
    assert observation.observation_version != "trace-graph-v1"


def test_persist_chain_event_uses_onchain_repository() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        chain_event = ChainEvent(
            event_type="large_transfer",
            txid="ff00",
            address="bc1qpersisted",
            value_sats=10_000,
            block_height=900001,
            observed_at=datetime(2026, 8, 14, tzinfo=UTC),
            payload={"provider": "bitcoin_core_rpc", "source_type": "rpc"},
        )
        batch = BitcoinObservationProducer(OnchainRepository(session)).persist_chain_event(
            chain_event,
            significance=0.5,
            confidence=0.8,
            explainability={"reason": "test"},
            tags=["large_transfer"],
        )
        assert batch.persisted_event is not None
        assert session.query(OnchainEvent).count() == 1
        assert batch.observations

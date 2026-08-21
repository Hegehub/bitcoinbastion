from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.onchain import OnchainEvent
from app.services.bastion_trace.graph.builder import TraceGraphBuilder
from app.services.bastion_trace.graph.domain import (
    TraceAnalyticalObjectKind,
    TraceRelationshipType,
)
from app.services.bastion_trace.graph.topology_adapter import BitcoinTopologyGraphAdapter
from app.services.bitcoin_observations.producer import BitcoinObservationProducer
from app.services.bitcoin_topology.domain import (
    BitcoinTopologyObjectType,
    stable_topology_object_id,
)
from app.services.bitcoin_topology.engine import BitcoinTopologyEngine
from app.services.bitcoin_topology.pipeline import BitcoinTopologyPipeline
from app.services.bitcoin_topology.relationship_producer import (
    BitcoinTopologyRelationshipProducer,
)


def _event(txid: str, address: str, minute: int = 0) -> OnchainEvent:
    return OnchainEvent(
        id=minute + 1,
        event_type="mempool_recent_tx",
        txid=txid,
        address=address,
        value_sats=2500,
        fee_sats=125,
        block_height=900000 + minute,
        observed_at=datetime(2026, 8, 14, 12, minute, tzinfo=UTC),
        provider="esplora",
        raw_payload_json=(
            '{"provider":"esplora","source_type":"provider",'
            '"network":"bitcoin-mainnet","private_provider_token":"never-project"}'
        ),
        confidence_score=0.91,
    )


def _snapshot(*events: OnchainEvent):
    snapshot = BitcoinTopologyPipeline().snapshot_for_events(events)
    assert snapshot is not None
    return snapshot


def test_identity_direction_taxonomy_and_projection_idempotency() -> None:
    snapshot = _snapshot(_event("aaaa", "bc1qa"), _event("bbbb", "bc1qb", 1))
    adapter = BitcoinTopologyGraphAdapter()
    first = adapter.project(snapshot)
    second = adapter.project(snapshot)
    assert first == second
    assert tuple(first.objects) == snapshot.node_ids
    assert tuple(first.relationships) == snapshot.relationship_ids
    for topology_relationship in snapshot.relationships.values():
        projected = first.relationships[topology_relationship.id]
        assert projected.source_id == topology_relationship.source.object_id
        assert projected.target_id == topology_relationship.target.object_id
        assert projected.relationship_type is TraceRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION
        assert projected.id == topology_relationship.id


def test_network_separation_and_typed_object_mapping() -> None:
    mainnet = stable_topology_object_id(
        BitcoinTopologyObjectType.ADDRESS, "same", network="bitcoin-mainnet"
    )
    testnet = stable_topology_object_id(
        BitcoinTopologyObjectType.ADDRESS, "same", network="bitcoin-testnet"
    )
    assert mainnet != testnet
    projection = BitcoinTopologyGraphAdapter().project(_snapshot(_event("aaaa", "bc1qa")))
    assert {item.kind for item in projection.objects.values()} == {
        TraceAnalyticalObjectKind.BITCOIN_ADDRESS,
        TraceAnalyticalObjectKind.BITCOIN_TRANSACTION,
    }


def test_end_to_end_provenance_and_graph_snapshot_correlation() -> None:
    event = _event("aaaa", "bc1qa")
    observations = BitcoinObservationProducer().from_onchain_event(event).observations
    relationships = BitcoinTopologyRelationshipProducer().produce(observations).relationships
    topology_snapshot = BitcoinTopologyEngine().build(relationships).snapshot()
    projection = BitcoinTopologyGraphAdapter().project(topology_snapshot)
    builder = TraceGraphBuilder()
    builder.add_topology_projection(projection)
    graph = builder.build()
    graph_snapshot = graph.snapshot()
    relationship = graph.relationships[relationships[0].id]

    assert graph_snapshot.topology_snapshot_id == topology_snapshot.topology_id
    assert relationship.provenance.source_relationship_id == relationships[0].id
    assert relationship.provenance.topology_snapshot_id == topology_snapshot.topology_id
    assert relationship.provenance.observations == relationships[0].provenance.originating_observation_ids
    assert set(relationship.provenance.observations) <= set(graph.observations)
    assert "authoritative_topology_producer_missing" not in graph.limitations
    assert "no_ownership_inference" in relationship.limitations


def test_historical_projection_has_no_future_data_leakage_and_is_immutable() -> None:
    first_event = _event("aaaa", "bc1qa")
    second_event = _event("bbbb", "bc1qa", 1)
    history = BitcoinTopologyPipeline().history_for_events((first_event, second_event)).snapshots
    assert len(history) == 2
    adapter = BitcoinTopologyGraphAdapter()
    first_projection = adapter.project(history[0])
    second_projection = adapter.project(history[1])
    assert len(first_projection.relationships) == 1
    assert len(second_projection.relationships) == 2
    first_relationship_ids = tuple(first_projection.relationships)
    assert set(first_relationship_ids) < set(second_projection.relationships)
    with pytest.raises(FrozenInstanceError):
        history[0].topology_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        first_projection.relationships["new"] = next(  # type: ignore[index]
            iter(second_projection.relationships.values())
        )
    assert tuple(first_projection.relationships) == first_relationship_ids


def test_pipeline_chronology_uses_source_time_not_input_order() -> None:
    first = _event("aaaa", "bc1qa")
    second = _event("bbbb", "bc1qb", 1)
    second.observed_at = first.observed_at + timedelta(minutes=1)
    history = BitcoinTopologyPipeline().history_for_events((second, first))
    assert len(history.snapshots[0].relationships) == 1
    assert len(history.snapshots[1].relationships) == 2

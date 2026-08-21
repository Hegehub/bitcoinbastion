from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.onchain import OnchainEvent
from app.services.bitcoin_observations.producer import BitcoinObservationProducer
from app.services.bitcoin_topology.engine import (
    TOPOLOGY_ENGINE_VERSION,
    TOPOLOGY_VERSION,
    BitcoinTopologyEngine,
    BitcoinTopologyEngineError,
)
from app.services.bitcoin_topology.relationship_producer import BitcoinTopologyRelationshipProducer


def event(txid: str, address: str, observed_at: datetime) -> OnchainEvent:
    return OnchainEvent(
        event_type="mempool_recent_tx",
        txid=txid,
        address=address,
        value_sats=2500,
        fee_sats=125,
        block_height=900000,
        observed_at=observed_at,
        provider="esplora",
        raw_payload_json='{"provider":"esplora","source_type":"provider"}',
        confidence_score=0.91,
    )


def relationship(txid: str = "ABCDEF1234", address: str = "bc1qexample", minutes: int = 0):
    observations = BitcoinObservationProducer().from_onchain_event(
        event(txid, address, datetime(2026, 8, 14, 12, minutes, tzinfo=UTC))
    ).observations
    return BitcoinTopologyRelationshipProducer().produce(observations).relationships[0]


def test_topology_determinism_and_identity_stability() -> None:
    rel_a = relationship("aaaa", "bc1qa")
    rel_b = relationship("bbbb", "bc1qb")
    engine = BitcoinTopologyEngine()
    first = engine.build((rel_a, rel_b))
    second = engine.build((rel_b, rel_a))
    assert first.topology_id == second.topology_id
    assert tuple(first.nodes) == tuple(second.nodes)
    assert first.snapshot() == second.snapshot()


def test_directed_path_reachability_and_adjacency() -> None:
    rel = relationship()
    topology = BitcoinTopologyEngine().build((rel,))
    engine = BitcoinTopologyEngine()
    assert engine.adjacency(topology, rel.source.object_id) == (rel.target.object_id,)
    assert engine.reachable(topology, rel.source.object_id, rel.target.object_id) is True
    assert engine.reachable(topology, rel.target.object_id, rel.source.object_id) is False
    assert engine.shortest_path(topology, rel.source.object_id, rel.target.object_id) == (
        rel.source.object_id,
        rel.target.object_id,
    )


def test_ancestor_descendant_traversal() -> None:
    rel = relationship()
    topology = BitcoinTopologyEngine().build((rel,))
    engine = BitcoinTopologyEngine()
    assert engine.descendants(topology, rel.source.object_id) == (rel.target.object_id,)
    assert engine.ancestors(topology, rel.target.object_id) == (rel.source.object_id,)


def test_component_discovery() -> None:
    rel_a = relationship("aaaa", "bc1qa")
    rel_b = relationship("bbbb", "bc1qb")
    components = BitcoinTopologyEngine().connected_components(
        BitcoinTopologyEngine().build((rel_a, rel_b))
    )
    assert len(components) == 2
    assert all(len(component) == 2 for component in components)


def test_snapshot_and_topology_are_immutable() -> None:
    rel = relationship()
    topology = BitcoinTopologyEngine().build((rel,))
    snapshot = topology.snapshot()
    assert snapshot.topology_version == TOPOLOGY_VERSION
    assert snapshot.engine_version == TOPOLOGY_ENGINE_VERSION
    with pytest.raises(FrozenInstanceError):
        snapshot.topology_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        topology.nodes["new"] = next(iter(topology.nodes.values()))  # type: ignore[index]


def test_validation_rejects_duplicate_relationships_and_broken_provenance() -> None:
    rel = relationship()
    engine = BitcoinTopologyEngine()
    with pytest.raises(BitcoinTopologyEngineError):
        engine.build((rel, rel))
    broken = replace(rel, provenance=replace(rel.provenance, originating_observation_ids=()))
    with pytest.raises(BitcoinTopologyEngineError):
        engine.build((broken,))


def test_temporal_filtering_is_authoritative_and_deterministic() -> None:
    first = relationship("aaaa", "bc1qa", minutes=0)
    second = relationship("bbbb", "bc1qb", minutes=10)
    filtered = BitcoinTopologyEngine().temporal_filter(
        (second, first), start=datetime(2026, 8, 14, 12, 5, tzinfo=UTC)
    )
    assert filtered == (second,)
    assert BitcoinTopologyEngine().temporal_filter(
        (second, first), end=datetime(2026, 8, 14, 12, 0, tzinfo=UTC) + timedelta(seconds=1)
    ) == (first,)


def test_incremental_rebuild_same_relationship_set_same_snapshot() -> None:
    rel = relationship()
    engine = BitcoinTopologyEngine()
    initial = engine.build((rel,))
    rebuilt = engine.build((*initial.relationships.values(),))
    assert initial.snapshot() == rebuilt.snapshot()

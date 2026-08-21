from __future__ import annotations

from dataclasses import dataclass

from app.db.models.onchain import OnchainEvent
from app.services.bitcoin_observations.producer import BitcoinObservationProducer
from app.services.bitcoin_topology.engine import BitcoinTopologyEngine, BitcoinTopologySnapshot
from app.services.bitcoin_topology.relationship_producer import (
    BitcoinTopologyRelationshipProducer,
)


@dataclass(frozen=True, slots=True)
class BitcoinTopologySnapshotHistory:
    snapshots: tuple[BitcoinTopologySnapshot, ...]


class BitcoinTopologyPipeline:
    """Canonical T1 -> T2 -> T3 orchestration over persisted source facts."""

    def __init__(self) -> None:
        self._observation_producer = BitcoinObservationProducer()
        self._relationship_producer = BitcoinTopologyRelationshipProducer()
        self._engine = BitcoinTopologyEngine()

    def snapshot_for_events(
        self, events: tuple[OnchainEvent, ...]
    ) -> BitcoinTopologySnapshot | None:
        observations = tuple(
            observation
            for event in events
            for observation in self._observation_producer.from_onchain_event(event).observations
        )
        relationships = self._relationship_producer.produce(observations).relationships
        if not relationships:
            return None
        return self._engine.build(relationships).snapshot()

    def history_for_events(
        self, events: tuple[OnchainEvent, ...]
    ) -> BitcoinTopologySnapshotHistory:
        ordered = tuple(sorted(events, key=lambda item: (item.observed_at, item.id)))
        snapshots: dict[str, BitcoinTopologySnapshot] = {}
        for index in range(1, len(ordered) + 1):
            snapshot = self.snapshot_for_events(ordered[:index])
            if snapshot is not None:
                snapshots[snapshot.topology_id] = snapshot
        return BitcoinTopologySnapshotHistory(snapshots=tuple(snapshots.values()))

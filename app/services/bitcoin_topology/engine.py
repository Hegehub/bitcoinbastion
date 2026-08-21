from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Mapping

from app.services.bitcoin_topology.domain import (
    BitcoinTopologyObjectRef,
    BitcoinTopologyRelationship,
)

TOPOLOGY_VERSION = "bitcoin-topology-v1"
TOPOLOGY_ENGINE_VERSION = "bitcoin-topology-engine-v1"


class BitcoinTopologyValidationCode(str, Enum):
    DUPLICATE_RELATIONSHIP = "duplicate_relationship"
    MISSING_OBJECT = "missing_object"
    BROKEN_PROVENANCE = "broken_provenance"
    EMPTY_RELATIONSHIP_ID = "empty_relationship_id"


@dataclass(frozen=True, slots=True)
class BitcoinTopologyValidationFailure:
    code: BitcoinTopologyValidationCode
    message: str
    identity: str = ""


class BitcoinTopologyEngineError(ValueError):
    def __init__(self, failures: tuple[BitcoinTopologyValidationFailure, ...]) -> None:
        self.failures = failures
        detail = "; ".join(f"{failure.code.value}:{failure.message}" for failure in failures)
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class BitcoinTopologyNode:
    object_ref: BitcoinTopologyObjectRef
    relationship_ids: tuple[str, ...]
    originating_observation_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BitcoinTopologySnapshot:
    topology_id: str
    topology_version: str
    engine_version: str
    network: str
    captured_at: datetime | None
    nodes: Mapping[str, BitcoinTopologyNode]
    relationships: Mapping[str, BitcoinTopologyRelationship]
    relationship_ids: tuple[str, ...]
    node_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BitcoinTopology:
    topology_id: str
    topology_version: str
    engine_version: str
    nodes: Mapping[str, BitcoinTopologyNode]
    relationships: Mapping[str, BitcoinTopologyRelationship]
    adjacency: Mapping[str, tuple[str, ...]]
    reverse_adjacency: Mapping[str, tuple[str, ...]]
    limitations: tuple[str, ...]

    def snapshot(self) -> BitcoinTopologySnapshot:
        captured_at = max(
            (relationship.created_at for relationship in self.relationships.values()),
            default=None,
        )
        networks = {node.object_ref.network for node in self.nodes.values()}
        return BitcoinTopologySnapshot(
            topology_id=self.topology_id,
            topology_version=self.topology_version,
            engine_version=self.engine_version,
            network=next(iter(networks), "bitcoin-mainnet"),
            captured_at=captured_at,
            nodes=MappingProxyType(dict(self.nodes)),
            relationships=MappingProxyType(dict(self.relationships)),
            relationship_ids=tuple(sorted(self.relationships)),
            node_ids=tuple(sorted(self.nodes)),
            limitations=self.limitations,
        )


class BitcoinTopologyEngine:
    """Constructs deterministic backend topology from authoritative relationships."""

    def build(
        self, relationships: tuple[BitcoinTopologyRelationship, ...]
    ) -> BitcoinTopology:
        self._validate_relationship_inputs(relationships)
        relationship_map = {item.id: item for item in relationships}
        nodes = self._build_nodes(relationship_map)
        adjacency, reverse_adjacency = self._build_adjacency(relationship_map, nodes)
        limitations = tuple(
            sorted({limit for item in relationships for limit in item.limitations})
        )
        topology_id = self._topology_id(tuple(sorted(relationship_map)))
        return BitcoinTopology(
            topology_id=topology_id,
            topology_version=TOPOLOGY_VERSION,
            engine_version=TOPOLOGY_ENGINE_VERSION,
            nodes=MappingProxyType(dict(sorted(nodes.items()))),
            relationships=MappingProxyType(dict(sorted(relationship_map.items()))),
            adjacency=MappingProxyType(dict(sorted(adjacency.items()))),
            reverse_adjacency=MappingProxyType(dict(sorted(reverse_adjacency.items()))),
            limitations=limitations,
        )

    def adjacency(self, topology: BitcoinTopology, node_id: str) -> tuple[str, ...]:
        return topology.adjacency.get(node_id, ())

    def descendants(self, topology: BitcoinTopology, node_id: str) -> tuple[str, ...]:
        return self._traverse(topology.adjacency, node_id)

    def ancestors(self, topology: BitcoinTopology, node_id: str) -> tuple[str, ...]:
        return self._traverse(topology.reverse_adjacency, node_id)

    def reachable(self, topology: BitcoinTopology, source_id: str, target_id: str) -> bool:
        return target_id in self.descendants(topology, source_id)

    def shortest_path(
        self, topology: BitcoinTopology, source_id: str, target_id: str
    ) -> tuple[str, ...]:
        if source_id not in topology.nodes or target_id not in topology.nodes:
            return ()
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(source_id, (source_id,))])
        visited = {source_id}
        while queue:
            current, path = queue.popleft()
            if current == target_id:
                return path
            for next_id in topology.adjacency.get(current, ()):
                if next_id in visited:
                    continue
                visited.add(next_id)
                queue.append((next_id, (*path, next_id)))
        return ()

    def connected_components(self, topology: BitcoinTopology) -> tuple[tuple[str, ...], ...]:
        remaining = set(topology.nodes)
        components: list[tuple[str, ...]] = []
        while remaining:
            start = sorted(remaining)[0]
            component = {start}
            queue = deque([start])
            while queue:
                current = queue.popleft()
                neighbors = set(topology.adjacency.get(current, ())) | set(
                    topology.reverse_adjacency.get(current, ())
                )
                for neighbor in sorted(neighbors):
                    if neighbor in component:
                        continue
                    component.add(neighbor)
                    queue.append(neighbor)
            remaining -= component
            components.append(tuple(sorted(component)))
        return tuple(sorted(components))

    def temporal_filter(
        self,
        relationships: tuple[BitcoinTopologyRelationship, ...],
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[BitcoinTopologyRelationship, ...]:
        filtered = []
        for relationship in relationships:
            if start is not None and relationship.created_at < start:
                continue
            if end is not None and relationship.created_at > end:
                continue
            filtered.append(relationship)
        return tuple(sorted(filtered, key=lambda item: item.id))

    def _validate_relationship_inputs(
        self, relationships: tuple[BitcoinTopologyRelationship, ...]
    ) -> None:
        failures: list[BitcoinTopologyValidationFailure] = []
        seen: set[str] = set()
        for relationship in relationships:
            if not relationship.id:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        BitcoinTopologyValidationCode.EMPTY_RELATIONSHIP_ID,
                        "relationship id is empty",
                    )
                )
            if relationship.id in seen:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        BitcoinTopologyValidationCode.DUPLICATE_RELATIONSHIP,
                        "duplicate relationship identity",
                        relationship.id,
                    )
                )
            seen.add(relationship.id)
            if not relationship.source.object_id or not relationship.target.object_id:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        BitcoinTopologyValidationCode.MISSING_OBJECT,
                        "relationship source or target object is missing",
                        relationship.id,
                    )
                )
            if relationship.source.network != relationship.target.network:
                failures.append(
                    BitcoinTopologyValidationFailure(
                        BitcoinTopologyValidationCode.MISSING_OBJECT,
                        "relationship endpoints belong to different Bitcoin networks",
                        relationship.id,
                    )
                )
            if (
                not relationship.provenance.producer
                or not relationship.provenance.builder_version
                or not relationship.provenance.originating_observation_ids
            ):
                failures.append(
                    BitcoinTopologyValidationFailure(
                        BitcoinTopologyValidationCode.BROKEN_PROVENANCE,
                        "relationship provenance is incomplete",
                        relationship.id,
                    )
                )
        if failures:
            raise BitcoinTopologyEngineError(tuple(failures))

    def _build_nodes(
        self, relationships: Mapping[str, BitcoinTopologyRelationship]
    ) -> dict[str, BitcoinTopologyNode]:
        refs: dict[str, BitcoinTopologyObjectRef] = {}
        rels: dict[str, set[str]] = {}
        observations: dict[str, set[str]] = {}
        limitations: dict[str, set[str]] = {}
        for relationship in relationships.values():
            for ref in (relationship.source, relationship.target):
                refs[ref.object_id] = ref
                rels.setdefault(ref.object_id, set()).add(relationship.id)
                observations.setdefault(ref.object_id, set()).update(
                    relationship.provenance.originating_observation_ids
                )
                limitations.setdefault(ref.object_id, set()).update(relationship.limitations)
        return {
            node_id: BitcoinTopologyNode(
                object_ref=refs[node_id],
                relationship_ids=tuple(sorted(rels[node_id])),
                originating_observation_ids=tuple(sorted(observations[node_id])),
                limitations=tuple(sorted(limitations[node_id])),
            )
            for node_id in sorted(refs)
        }

    def _build_adjacency(
        self,
        relationships: Mapping[str, BitcoinTopologyRelationship],
        nodes: Mapping[str, BitcoinTopologyNode],
    ) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
        adjacency_sets: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        reverse_sets: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        for relationship in relationships.values():
            adjacency_sets[relationship.source.object_id].add(relationship.target.object_id)
            reverse_sets[relationship.target.object_id].add(relationship.source.object_id)
        return (
            {key: tuple(sorted(value)) for key, value in adjacency_sets.items()},
            {key: tuple(sorted(value)) for key, value in reverse_sets.items()},
        )

    def _traverse(self, adjacency: Mapping[str, tuple[str, ...]], node_id: str) -> tuple[str, ...]:
        visited: set[str] = set()
        queue = deque(adjacency.get(node_id, ()))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(adjacency.get(current, ()))
        return tuple(sorted(visited))

    def _topology_id(self, relationship_ids: tuple[str, ...]) -> str:
        raw = "\x1f".join((TOPOLOGY_VERSION, TOPOLOGY_ENGINE_VERSION, *relationship_ids))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return f"bitcoin_topology:{digest}"

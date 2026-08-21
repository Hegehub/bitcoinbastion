from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.services.bastion_trace.graph.domain import (
    TraceAnalyticalObject,
    TraceAnalyticalObjectKind,
    TraceEvidenceReference,
    TraceObservation,
    TraceObservationKind,
    TraceProvenance,
    TraceRelationship,
    TraceRelationshipDirection,
    TraceRelationshipType,
)
from app.services.bitcoin_topology.domain import (
    BitcoinTopologyDirection,
    BitcoinTopologyObjectType,
    BitcoinTopologyRelationshipType,
)
from app.services.bitcoin_topology.engine import BitcoinTopologySnapshot

ADAPTER_VERSION = "bitcoin-topology-graph-adapter-v1"


class TopologyGraphMappingError(ValueError):
    """Raised when topology cannot be represented without changing its semantics."""


class TopologyGraphTaxonomyCompatibility(str, Enum):
    DIRECTLY_COMPATIBLE = "directly_compatible"
    NOT_GRAPH_PROJECTABLE = "not_graph_projectable"


@dataclass(frozen=True, slots=True)
class TopologyGraphProjection:
    topology_snapshot_id: str
    topology_version: str
    topology_engine_version: str
    network: str
    objects: Mapping[str, TraceAnalyticalObject]
    relationships: Mapping[str, TraceRelationship]
    observation_references: Mapping[str, TraceObservation]
    limitations: tuple[str, ...]


class BitcoinTopologyGraphAdapter:
    """The single semantic boundary from finalized Bitcoin topology into Trace Graph."""

    _OBJECT_TYPES = {
        BitcoinTopologyObjectType.ADDRESS: TraceAnalyticalObjectKind.BITCOIN_ADDRESS,
        BitcoinTopologyObjectType.TRANSACTION: TraceAnalyticalObjectKind.BITCOIN_TRANSACTION,
    }
    _RELATIONSHIP_TYPES = {
        BitcoinTopologyRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION:
            TraceRelationshipType.ADDRESS_PARTICIPATES_IN_TRANSACTION,
    }

    def project(self, snapshot: BitcoinTopologySnapshot) -> TopologyGraphProjection:
        self._validate(snapshot)
        observation_ids = {
            observation_id
            for relationship in snapshot.relationships.values()
            for observation_id in relationship.provenance.originating_observation_ids
        }
        observation_refs = {
            observation_id: self._observation_reference(observation_id, snapshot)
            for observation_id in sorted(observation_ids)
        }
        objects = {
            node_id: self._object(node_id, snapshot)
            for node_id in sorted(snapshot.nodes)
        }
        relationships = {
            relationship_id: self._relationship(relationship_id, snapshot)
            for relationship_id in sorted(snapshot.relationships)
        }
        return TopologyGraphProjection(
            topology_snapshot_id=snapshot.topology_id,
            topology_version=snapshot.topology_version,
            topology_engine_version=snapshot.engine_version,
            network=snapshot.network,
            objects=MappingProxyType(objects),
            relationships=MappingProxyType(relationships),
            observation_references=MappingProxyType(observation_refs),
            limitations=tuple(sorted(set(snapshot.limitations) | {"topology_projection"})),
        )

    def taxonomy_compatibility(
        self, relationship_type: BitcoinTopologyRelationshipType
    ) -> TopologyGraphTaxonomyCompatibility:
        if relationship_type in self._RELATIONSHIP_TYPES:
            return TopologyGraphTaxonomyCompatibility.DIRECTLY_COMPATIBLE
        return TopologyGraphTaxonomyCompatibility.NOT_GRAPH_PROJECTABLE

    def _validate(self, snapshot: BitcoinTopologySnapshot) -> None:
        for node in snapshot.nodes.values():
            if node.object_ref.object_type not in self._OBJECT_TYPES:
                raise TopologyGraphMappingError(
                    f"unsupported topology object type: {node.object_ref.object_type.value}"
                )
            if node.object_ref.network != snapshot.network:
                raise TopologyGraphMappingError("topology node network differs from snapshot network")
        for relationship in snapshot.relationships.values():
            if relationship.relationship_type not in self._RELATIONSHIP_TYPES:
                raise TopologyGraphMappingError(
                    "unsupported topology relationship type: "
                    f"{relationship.relationship_type.value}"
                )
            if relationship.direction is not BitcoinTopologyDirection.DIRECTED:
                raise TopologyGraphMappingError("unsupported topology relationship direction")
            if relationship.source.object_id not in snapshot.nodes:
                raise TopologyGraphMappingError("topology relationship source is absent")
            if relationship.target.object_id not in snapshot.nodes:
                raise TopologyGraphMappingError("topology relationship target is absent")

    def _object(
        self, node_id: str, snapshot: BitcoinTopologySnapshot
    ) -> TraceAnalyticalObject:
        node = snapshot.nodes[node_id]
        return TraceAnalyticalObject(
            id=node.object_ref.object_id,
            kind=self._OBJECT_TYPES[node.object_ref.object_type],
            label=node.object_ref.value,
            provenance=TraceProvenance(
                producer=ADAPTER_VERSION,
                stage="topology_to_graph",
                observations=node.originating_observation_ids,
                limitations=node.limitations,
                topology_snapshot_id=snapshot.topology_id,
            ),
            limitations=node.limitations,
        )

    def _relationship(
        self, relationship_id: str, snapshot: BitcoinTopologySnapshot
    ) -> TraceRelationship:
        relationship = snapshot.relationships[relationship_id]
        observation_ids = relationship.provenance.originating_observation_ids
        evidence = TraceEvidenceReference(
            reference=relationship.id,
            source_name=relationship.provenance.source.source_name,
            source_type=relationship.provenance.source.source_type,
        )
        return TraceRelationship(
            id=relationship.id,
            source_id=relationship.source.object_id,
            target_id=relationship.target.object_id,
            relationship_type=self._RELATIONSHIP_TYPES[relationship.relationship_type],
            direction=TraceRelationshipDirection.DIRECTED,
            originating_observation_id=observation_ids[0],
            provenance=TraceProvenance(
                producer=ADAPTER_VERSION,
                stage="topology_to_graph",
                observations=observation_ids,
                evidence=(evidence,),
                limitations=relationship.limitations,
                source_relationship_id=relationship.id,
                topology_snapshot_id=snapshot.topology_id,
            ),
            limitations=relationship.limitations,
        )

    def _observation_reference(
        self, observation_id: str, snapshot: BitcoinTopologySnapshot
    ) -> TraceObservation:
        return TraceObservation(
            id=observation_id,
            kind=TraceObservationKind.BITCOIN_OBSERVATION_REFERENCE,
            subject="bitcoin_observation",
            value="reference_only",
            provenance=TraceProvenance(
                producer=ADAPTER_VERSION,
                stage="topology_to_graph",
                topology_snapshot_id=snapshot.topology_id,
                limitations=("reference_only",),
            ),
            limitations=("reference_only",),
        )

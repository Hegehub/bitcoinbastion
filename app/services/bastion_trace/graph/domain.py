from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Mapping, TypeVar


GRAPH_VERSION = "trace-graph-v1"


class TraceObservationKind(str, Enum):
    RAW_SUBJECT = "raw_subject"
    DERIVED_FACT = "derived_fact"
    BITCOIN_OBSERVATION_REFERENCE = "bitcoin_observation_reference"


class TraceAnalyticalObjectKind(str, Enum):
    BITCOIN_ADDRESS = "bitcoin_address"
    BITCOIN_TRANSACTION = "bitcoin_transaction"
    TRACE_REPORT = "trace_report"


class TraceRelationshipType(str, Enum):
    ANALYZED_AS = "analyzed_as"
    ADDRESS_PARTICIPATES_IN_TRANSACTION = "address_participates_in_transaction"


class TraceRelationshipDirection(str, Enum):
    DIRECTED = "directed"


@dataclass(frozen=True, slots=True)
class TraceEvidenceReference:
    reference: str
    source_name: str
    source_type: str


@dataclass(frozen=True, slots=True)
class TraceProvenance:
    producer: str
    stage: str
    observations: tuple[str, ...] = ()
    evidence: tuple[TraceEvidenceReference, ...] = ()
    limitations: tuple[str, ...] = ()
    source_relationship_id: str | None = None
    topology_snapshot_id: str | None = None


@dataclass(frozen=True, slots=True)
class TraceObservation:
    id: str
    kind: TraceObservationKind
    subject: str
    value: str
    provenance: TraceProvenance
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceAnalyticalObject:
    id: str
    kind: TraceAnalyticalObjectKind
    label: str
    provenance: TraceProvenance
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceRelationship:
    id: str
    source_id: str
    target_id: str
    relationship_type: TraceRelationshipType
    direction: TraceRelationshipDirection
    originating_observation_id: str
    provenance: TraceProvenance
    confidence: float | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceReportProjectionFacts:
    id: int | None
    address: str
    summary: str
    chain: str
    trace_score: float
    trace_band: str
    confidence: float
    source_quality: str
    freshness: str
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    operator_guidance: tuple[str, ...] = ()
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    provenance: TraceProvenance = TraceProvenance(
        producer="TraceGraphBuilder", stage="report_projection"
    )


@dataclass(frozen=True, slots=True)
class TraceGraphMetadata:
    graph_version: str = GRAPH_VERSION
    analysis_version: str = "baseline-trace-v1"
    chain: str = "bitcoin"
    graph_hash: str = ""
    topology_snapshot_id: str | None = None
    topology_version: str | None = None
    topology_engine_version: str | None = None
    topology_network: str | None = None


@dataclass(frozen=True, slots=True)
class TraceGraph:
    objects: Mapping[str, TraceAnalyticalObject]
    relationships: Mapping[str, TraceRelationship]
    observations: Mapping[str, TraceObservation]
    report_facts: Mapping[str, TraceReportProjectionFacts]
    metadata: TraceGraphMetadata
    limitations: tuple[str, ...] = ()

    def snapshot(self) -> TraceSnapshot:
        return TraceSnapshot.from_graph(self)


@dataclass(frozen=True, slots=True)
class TraceSnapshot:
    graph_version: str
    analysis_version: str
    graph_hash: str
    object_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]
    report_fact_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    topology_snapshot_id: str | None

    @classmethod
    def from_graph(cls, graph: TraceGraph) -> TraceSnapshot:
        return cls(
            graph_version=graph.metadata.graph_version,
            analysis_version=graph.metadata.analysis_version,
            graph_hash=graph.metadata.graph_hash,
            object_ids=tuple(sorted(graph.objects)),
            relationship_ids=tuple(sorted(graph.relationships)),
            observation_ids=tuple(sorted(graph.observations)),
            report_fact_ids=tuple(sorted(graph.report_facts)),
            limitations=tuple(graph.limitations),
            topology_snapshot_id=graph.metadata.topology_snapshot_id,
        )


def stable_trace_id(namespace: str, *parts: str) -> str:
    raw = "\x1f".join((namespace, *parts))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{namespace}:{digest}"


T = TypeVar("T")


def immutable_mapping(items: Mapping[str, T]) -> Mapping[str, T]:
    return MappingProxyType(dict(sorted(items.items())))

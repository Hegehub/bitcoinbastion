from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib

from app.schemas.bastion_trace import TraceReport
from app.services.bastion_trace.graph.domain import (
    TraceAnalyticalObject,
    TraceAnalyticalObjectKind,
    TraceGraph,
    TraceGraphMetadata,
    TraceObservation,
    TraceReportProjectionFacts,
    TraceObservationKind,
    TraceProvenance,
    TraceRelationship,
    TraceRelationshipDirection,
    TraceRelationshipType,
    immutable_mapping,
    stable_trace_id,
)

GRAPH_RELATIONSHIP_PRODUCER_MISSING = "authoritative_topology_producer_missing"


class TraceGraphStage(str, Enum):
    OBSERVATION_COLLECTION = "observation_collection"
    OBSERVATION_NORMALIZATION = "observation_normalization"
    IDENTITY_RESOLUTION = "identity_resolution"
    OBJECT_CREATION = "object_creation"
    RELATIONSHIP_CONSTRUCTION = "relationship_construction"
    EVIDENCE_LINKING = "evidence_linking"
    GRAPH_VALIDATION = "graph_validation"
    GRAPH_FINALIZATION = "graph_finalization"
    REPORT_PROJECTION = "report_projection"


@dataclass(frozen=True, slots=True)
class TraceGraphValidationFailure:
    stage: TraceGraphStage
    message: str
    identity: str = ""


class TraceGraphBuildError(ValueError):
    def __init__(self, failures: tuple[TraceGraphValidationFailure, ...]) -> None:
        self.failures = failures
        detail = "; ".join(f"{failure.stage.value}:{failure.message}" for failure in failures)
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class TraceReportObservationBundle:
    report: TraceReport


@dataclass(frozen=True, slots=True)
class NormalizedTraceObservationBundle:
    report: TraceReport
    address: str
    limitations: tuple[str, ...]
    subject_observation_id: str
    scoring_observation_id: str
    address_object_id: str
    report_object_id: str | None
    relationship_id: str | None


@dataclass(frozen=True, slots=True)
class TraceGraphPipelineState:
    bundles: tuple[TraceReportObservationBundle, ...] = ()
    normalized: tuple[NormalizedTraceObservationBundle, ...] = ()
    observations: dict[str, TraceObservation] | None = None
    objects: dict[str, TraceAnalyticalObject] | None = None
    relationships: dict[str, TraceRelationship] | None = None
    report_facts: dict[str, TraceReportProjectionFacts] | None = None
    limitations: tuple[str, ...] = ()


class TraceGraphBuilder:
    """Canonical backend producer for immutable Trace graphs."""

    def __init__(self, *, analysis_version: str = "baseline-trace-v1") -> None:
        self._analysis_version = analysis_version
        self._bundles: dict[str, TraceReportObservationBundle] = {}

    def add_report_projection(self, report: TraceReport) -> None:
        address = report.address.strip()
        bundle_id = stable_trace_id(
            "trace_observation_bundle",
            address,
            str(report.id or "pending"),
            report.trace_band.value,
            str(report.trace_score),
        )
        self._bundles[bundle_id] = TraceReportObservationBundle(report=report)

    def build(self) -> TraceGraph:
        state = self._collect_observations()
        state = self._normalize_observations(state)
        state = self._resolve_identities(state)
        state = self._create_objects(state)
        state = self._construct_relationships(state)
        state = self._link_evidence(state)
        self._validate_graph(state)
        return self._finalize_graph(state)

    def _collect_observations(self) -> TraceGraphPipelineState:
        return TraceGraphPipelineState(bundles=tuple(self._bundles[key] for key in sorted(self._bundles)))

    def _normalize_observations(
        self, state: TraceGraphPipelineState
    ) -> TraceGraphPipelineState:
        normalized: list[NormalizedTraceObservationBundle] = []
        failures: list[TraceGraphValidationFailure] = []
        for bundle in state.bundles:
            address = bundle.report.address.strip()
            if not address:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.OBSERVATION_NORMALIZATION,
                        "trace report observation address is empty",
                    )
                )
                continue
            limitations = tuple(sorted(set(bundle.report.limitations)))
            subject_observation_id = stable_trace_id("trace_observation", "raw_subject", address)
            scoring_observation_id = stable_trace_id(
                "trace_observation",
                "derived_fact",
                address,
                bundle.report.trace_band.value,
                str(bundle.report.trace_score),
            )
            address_object_id = stable_trace_id(
                "trace_object", TraceAnalyticalObjectKind.BITCOIN_ADDRESS.value, address
            )
            report_object_id = None
            relationship_id = None
            if bundle.report.id is not None:
                report_object_id = stable_trace_id(
                    "trace_object", TraceAnalyticalObjectKind.TRACE_REPORT.value, str(bundle.report.id)
                )
                relationship_id = stable_trace_id(
                    "trace_relationship",
                    TraceRelationshipType.ANALYZED_AS.value,
                    address_object_id,
                    report_object_id,
                    scoring_observation_id,
                )
            normalized.append(
                NormalizedTraceObservationBundle(
                    report=bundle.report,
                    address=address,
                    limitations=limitations,
                    subject_observation_id=subject_observation_id,
                    scoring_observation_id=scoring_observation_id,
                    address_object_id=address_object_id,
                    report_object_id=report_object_id,
                    relationship_id=relationship_id,
                )
            )
        if failures:
            raise TraceGraphBuildError(tuple(failures))
        return replace(state, normalized=tuple(normalized))

    def _resolve_identities(self, state: TraceGraphPipelineState) -> TraceGraphPipelineState:
        return state

    def _create_objects(self, state: TraceGraphPipelineState) -> TraceGraphPipelineState:
        observations: dict[str, TraceObservation] = {}
        objects: dict[str, TraceAnalyticalObject] = {}
        report_facts: dict[str, TraceReportProjectionFacts] = {}
        limitations = set(state.limitations)
        for item in state.normalized:
            observations[item.subject_observation_id] = TraceObservation(
                id=item.subject_observation_id,
                kind=TraceObservationKind.RAW_SUBJECT,
                subject=item.address,
                value=item.address,
                provenance=TraceProvenance(
                    producer="TraceService.analyze_address",
                    stage=TraceGraphStage.OBSERVATION_COLLECTION.value,
                    limitations=item.limitations,
                ),
                limitations=item.limitations,
            )
            observations[item.scoring_observation_id] = TraceObservation(
                id=item.scoring_observation_id,
                kind=TraceObservationKind.DERIVED_FACT,
                subject=item.address,
                value=f"{item.report.trace_band.value}:{item.report.trace_score}",
                provenance=TraceProvenance(
                    producer="score_trace",
                    stage=TraceGraphStage.OBSERVATION_NORMALIZATION.value,
                    observations=(item.subject_observation_id,),
                    limitations=item.limitations,
                ),
                limitations=item.limitations,
            )
            objects[item.address_object_id] = TraceAnalyticalObject(
                id=item.address_object_id,
                kind=TraceAnalyticalObjectKind.BITCOIN_ADDRESS,
                label=item.address,
                provenance=TraceProvenance(
                    producer="TraceService.analyze_address",
                    stage=TraceGraphStage.OBJECT_CREATION.value,
                    observations=(item.subject_observation_id,),
                    limitations=item.limitations,
                ),
                limitations=item.limitations,
            )
            report_fact_key = item.report_object_id or stable_trace_id(
                "trace_object", TraceAnalyticalObjectKind.TRACE_REPORT.value, item.address, "pending"
            )
            report_facts[report_fact_key] = TraceReportProjectionFacts(
                id=item.report.id,
                address=item.address,
                summary=item.report.summary,
                chain=item.report.chain,
                trace_score=item.report.trace_score,
                trace_band=item.report.trace_band.value,
                confidence=item.report.confidence,
                source_quality=item.report.source_quality.value,
                freshness=item.report.freshness.value,
                reason_codes=tuple(item.report.reason_codes),
                evidence_refs=tuple(item.report.evidence_refs),
                limitations=item.limitations,
                operator_guidance=tuple(item.report.operator_guidance),
                advisory_not_legal_verdict=item.report.advisory_not_legal_verdict,
                not_consensus_proof=item.report.not_consensus_proof,
                no_custody=item.report.no_custody,
                provenance=TraceProvenance(
                    producer="TraceGraphBuilder",
                    stage=TraceGraphStage.REPORT_PROJECTION.value,
                    observations=(item.scoring_observation_id,),
                    limitations=item.limitations,
                ),
            )
            if item.report_object_id is not None and item.report.id is not None:
                objects[item.report_object_id] = TraceAnalyticalObject(
                    id=item.report_object_id,
                    kind=TraceAnalyticalObjectKind.TRACE_REPORT,
                    label=f"trace_report:{item.report.id}",
                    provenance=TraceProvenance(
                        producer="TraceGraphBuilder",
                        stage=TraceGraphStage.REPORT_PROJECTION.value,
                        observations=(item.scoring_observation_id,),
                        limitations=item.limitations,
                    ),
                    limitations=item.limitations,
                )
            limitations.add(GRAPH_RELATIONSHIP_PRODUCER_MISSING)
        return replace(
            state,
            observations=observations,
            objects=objects,
            report_facts=report_facts,
            limitations=tuple(sorted(limitations)),
        )

    def _construct_relationships(self, state: TraceGraphPipelineState) -> TraceGraphPipelineState:
        relationships: dict[str, TraceRelationship] = {}
        for item in state.normalized:
            if item.report_object_id is None or item.relationship_id is None:
                continue
            relationships[item.relationship_id] = TraceRelationship(
                id=item.relationship_id,
                source_id=item.address_object_id,
                target_id=item.report_object_id,
                relationship_type=TraceRelationshipType.ANALYZED_AS,
                direction=TraceRelationshipDirection.DIRECTED,
                originating_observation_id=item.scoring_observation_id,
                provenance=TraceProvenance(
                    producer="TraceGraphBuilder",
                    stage=TraceGraphStage.RELATIONSHIP_CONSTRUCTION.value,
                    observations=(item.scoring_observation_id,),
                    limitations=item.limitations,
                ),
                confidence=item.report.confidence,
                limitations=item.limitations,
            )
        return replace(state, relationships=relationships)

    def _link_evidence(self, state: TraceGraphPipelineState) -> TraceGraphPipelineState:
        return state

    def _validate_graph(self, state: TraceGraphPipelineState) -> None:
        observations = state.observations or {}
        objects = state.objects or {}
        relationships = state.relationships or {}
        failures: list[TraceGraphValidationFailure] = []
        for observation in observations.values():
            if not observation.provenance.producer or not observation.provenance.stage:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "observation provenance is incomplete",
                        observation.id,
                    )
                )
        for obj in objects.values():
            if not obj.provenance.producer or not obj.provenance.stage:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "object provenance is incomplete",
                        obj.id,
                    )
                )
            for observation_id in obj.provenance.observations:
                if observation_id not in observations:
                    failures.append(
                        TraceGraphValidationFailure(
                            TraceGraphStage.GRAPH_VALIDATION,
                            "object references missing observation",
                            obj.id,
                        )
                    )
        for relationship in relationships.values():
            if relationship.source_id not in objects or relationship.target_id not in objects:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "relationship references missing object",
                        relationship.id,
                    )
                )
            if relationship.originating_observation_id not in observations:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "relationship references missing originating observation",
                        relationship.id,
                    )
                )
            if relationship.direction is not TraceRelationshipDirection.DIRECTED:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "relationship direction is unsupported",
                        relationship.id,
                    )
                )
            if relationship.relationship_type is not TraceRelationshipType.ANALYZED_AS:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "relationship type is unsupported",
                        relationship.id,
                    )
                )
            if not relationship.provenance.producer or not relationship.provenance.stage:
                failures.append(
                    TraceGraphValidationFailure(
                        TraceGraphStage.GRAPH_VALIDATION,
                        "relationship provenance is incomplete",
                        relationship.id,
                    )
                )
        if failures:
            raise TraceGraphBuildError(tuple(failures))

    def _finalize_graph(self, state: TraceGraphPipelineState) -> TraceGraph:
        objects = immutable_mapping(state.objects or {})
        relationships = immutable_mapping(state.relationships or {})
        observations = immutable_mapping(state.observations or {})
        report_facts = immutable_mapping(state.report_facts or {})
        graph_hash = self._graph_hash(objects, relationships, observations, report_facts, state.limitations)
        return TraceGraph(
            objects=objects,
            relationships=relationships,
            observations=observations,
            report_facts=report_facts,
            metadata=TraceGraphMetadata(
                analysis_version=self._analysis_version,
                graph_hash=graph_hash,
            ),
            limitations=tuple(sorted(state.limitations)),
        )

    def _graph_hash(
        self,
        objects: object,
        relationships: object,
        observations: object,
        report_facts: object,
        limitations: tuple[str, ...],
    ) -> str:
        payload = repr((objects, relationships, observations, report_facts, limitations, self._analysis_version))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

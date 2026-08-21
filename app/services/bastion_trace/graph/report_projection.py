from __future__ import annotations

from datetime import datetime

from app.schemas.bastion_trace import TraceBand, TraceFreshness, TraceReport, TraceSourceQuality
from app.services.bastion_trace.graph.builder import TraceGraphBuilder
from app.services.bastion_trace.graph.domain import TraceGraph, TraceReportProjectionFacts


class TraceReportGraphProjectionService:
    """Projects existing Trace report DTOs from graph-owned analytical facts."""

    def build_graph_for_report(self, report: TraceReport) -> TraceGraph:
        builder = TraceGraphBuilder()
        builder.add_report_projection(report)
        return builder.build()

    def project_report(
        self, graph: TraceGraph, *, created_at: datetime | None = None
    ) -> TraceReport:
        facts = self._single_report_facts(graph)
        return TraceReport(
            id=facts.id,
            address=facts.address,
            summary=facts.summary,
            chain=facts.chain,
            trace_score=facts.trace_score,
            trace_band=TraceBand(facts.trace_band),
            confidence=facts.confidence,
            source_quality=TraceSourceQuality(facts.source_quality),
            freshness=TraceFreshness(facts.freshness),
            reason_codes=list(facts.reason_codes),
            evidence_refs=list(facts.evidence_refs),
            limitations=list(facts.limitations),
            operator_guidance=list(facts.operator_guidance),
            advisory_not_legal_verdict=facts.advisory_not_legal_verdict,
            not_consensus_proof=facts.not_consensus_proof,
            no_custody=facts.no_custody,
            created_at=created_at,
        )

    def project_compatible_report(self, report: TraceReport, graph: TraceGraph) -> TraceReport:
        projected = self.project_report(graph, created_at=report.created_at)
        if report.id is not None and projected.id != report.id:
            msg = "graph report projection identity does not match report"
            raise ValueError(msg)
        return projected

    def _single_report_facts(self, graph: TraceGraph) -> TraceReportProjectionFacts:
        facts = tuple(graph.report_facts.values())
        if len(facts) != 1:
            msg = "graph must contain exactly one report projection fact"
            raise ValueError(msg)
        return facts[0]

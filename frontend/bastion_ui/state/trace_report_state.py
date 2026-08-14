from __future__ import annotations

import reflex as rx

from bastion_ui.domain.prompt12 import adapt_trace_report
from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.services.trace_client import TraceApiClient


class TraceReportState(rx.State):
    """Safe report projection; raw transport bodies never enter Reflex State."""

    trace_report_id: str = ""
    loading: bool = False
    error: str = ""
    route_validated: bool = False
    route_valid: bool = False
    subject_label: str = "Unavailable"
    chain_label: str = "Unavailable"
    report_status_label: str = "Unavailable"
    generated_at_label: str = "Unavailable"
    advisory_band_label: str = "Unavailable"
    trace_score_label: str = "Unavailable"
    confidence_label: str = "Unavailable"
    source_quality_label: str = "Unavailable"
    freshness_label: str = "Unavailable"
    summary_label: str = "Unavailable"
    limitations_label: str = "Limitations unavailable."
    evidence_label: str = "No Evidence references were supplied."
    has_degraded_data: bool = False
    has_provider_disagreement: bool = False
    has_limited_evidence: bool = True
    proof_packet_available: bool = False
    proof_packet_status_label: str = "Proof Packet belongs to Prompt 14 and is not loaded here."
    failed_panels: list[str] = []

    def set_report_id(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        self.trace_report_id = validation.report_id if validation.ok else ""
        self.error = "" if validation.ok else validation.error

    def validate_current_route(self) -> None:
        self.set_report_id(self.router.page.params.get("report_id", ""))
        self.route_valid = bool(self.trace_report_id)
        self.route_validated = True

    def invalidate_route(self) -> None:
        self.route_validated = False
        self.route_valid = False
        self.trace_report_id = ""

    async def load_trace_report(self) -> None:
        if not self.trace_report_id:
            self.error = "Report not found."
            return
        self.loading = True
        self.error = ""
        result = await TraceApiClient().get_trace_report(self.trace_report_id)
        if not result.ok:
            self.error = result.error or "Trace report is unavailable."
            self.has_degraded_data = True
            self.loading = False
            return
        try:
            report = adapt_trace_report(result.data)
        except (KeyError, TypeError, ValueError):
            self.error = "Trace report contract is unavailable."
            self.has_degraded_data = True
            self.loading = False
            return
        self.subject_label = report.subject
        self.chain_label = report.chain
        self.report_status_label = report.status
        self.generated_at_label = report.created_at
        self.advisory_band_label = report.advisory_band
        self.trace_score_label = str(report.score)
        self.confidence_label = str(report.confidence)
        self.source_quality_label = report.source_quality
        self.freshness_label = report.freshness
        self.summary_label = report.summary or "No backend summary was provided."
        self.limitations_label = (
            "Limitations: " + "; ".join(report.limitations)
            if report.limitations
            else "No limitations were supplied by the backend."
        )
        self.evidence_label = (
            "Evidence references: " + "; ".join(report.evidence_references)
            if report.evidence_references
            else "No Evidence references were supplied."
        )
        self.has_limited_evidence = not bool(report.evidence_references)
        self.loading = False

    def clear_error(self) -> None:
        self.error = ""

    def reset_report(self) -> None:
        self.trace_report_id = ""
        self.loading = False
        self.error = ""
        self.subject_label = "Unavailable"
        self.summary_label = "Unavailable"

from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.services.models import ApiResult
from bastion_ui.services.trace_client import TraceApiClient

REPORT_UNAVAILABLE_MESSAGE = "Trace data is temporarily unavailable."
PANEL_UNAVAILABLE_MESSAGE = "This panel could not be loaded."


def _as_dict(result: ApiResult) -> dict[str, Any]:
    return result.data if result.ok and isinstance(result.data, dict) else {}


class TraceReportState(rx.State):
    trace_report_id: str = ""
    loading: bool = False
    error: str = ""

    summary: dict[str, Any] = {}
    report: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    privacy_shield: dict[str, Any] = {}
    origin_passport: dict[str, Any] = {}
    source_summary: dict[str, Any] = {}
    provider_disagreement: dict[str, Any] = {}
    utxo_hygiene: dict[str, Any] = {}
    dust_radar: dict[str, Any] = {}
    counterparty_lens: dict[str, Any] = {}
    policy_facts: dict[str, Any] = {}
    proof_packet: dict[str, Any] = {}

    has_degraded_data: bool = False
    has_provider_disagreement: bool = False
    has_limited_evidence: bool = False
    proof_packet_available: bool = False
    failed_panels: list[str] = []

    report_status_label: str = "Not available"
    generated_at_label: str = "Not available"
    advisory_band_label: str = "Not available"
    confidence_label: str = "Not available"
    summary_label: str = "Not available"
    evidence_label: str = "Evidence unavailable. Manual review recommended."
    proof_packet_status_label: str = "Proof packet is not available for this report."

    def set_report_id(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        if not validation.ok:
            self.trace_report_id = ""
            self.error = validation.error
            return
        self.trace_report_id = validation.report_id
        self.error = ""

    async def load_trace_summary(self) -> None:
        if not self.trace_report_id:
            self.error = "Report not found."
            return
        result = await TraceApiClient().get_public_trace_summary(self.trace_report_id)
        if result.ok:
            self.summary = _as_dict(result)
        else:
            self.has_degraded_data = True
            self.failed_panels.append("summary")

    async def load_trace_evidence(self) -> None:
        if not self.trace_report_id:
            return
        result = await TraceApiClient().get_trace_evidence(self.trace_report_id)
        if result.ok:
            self.evidence = _as_dict(result)
        else:
            self.has_degraded_data = True
            self.has_limited_evidence = True
            self.failed_panels.append("evidence")

    async def load_trace_panels(self) -> None:
        if not self.trace_report_id:
            return
        client = TraceApiClient()
        panel_results = {
            "report": await client.get_trace_report(self.trace_report_id),
            "privacy_shield": await client.get_privacy_shield(self.trace_report_id),
            "origin_passport": await client.get_origin_passport(self.trace_report_id),
            "source_summary": await client.get_source_summary(self.trace_report_id),
            "provider_disagreement": await client.get_provider_disagreement(self.trace_report_id),
            "utxo_hygiene": await client.get_utxo_hygiene(self.trace_report_id),
            "dust_radar": await client.get_dust_radar(self.trace_report_id),
            "counterparty_lens": await client.get_counterparty_lens(self.trace_report_id),
            "policy_facts": await client.get_policy_facts(self.trace_report_id),
        }
        for name, result in panel_results.items():
            if result.ok:
                setattr(self, name, _as_dict(result))
                if result.degraded:
                    self.has_degraded_data = True
            else:
                self.has_degraded_data = True
                self.failed_panels.append(name)
        self.has_provider_disagreement = bool(self.provider_disagreement)

    async def load_trace_report(self) -> None:
        if not self.trace_report_id:
            self.error = "Report not found."
            return
        self.loading = True
        self.clear_error()
        self.failed_panels = []
        try:
            await self.load_trace_summary()
            await self.load_trace_evidence()
            await self.load_trace_panels()
            self._derive_labels()
        finally:
            self.loading = False

    async def load_proof_packet(self) -> None:
        if not self.trace_report_id:
            self.error = "Report not found."
            return
        self.loading = True
        self.clear_error()
        result = await TraceApiClient().get_proof_packet(self.trace_report_id)
        if result.ok:
            self.proof_packet = _as_dict(result)
            self.proof_packet_available = bool(self.proof_packet)
            self.proof_packet_status_label = (
                "Proof packet metadata loaded. Review limitations before relying on it."
                if self.proof_packet_available
                else "Proof packet is not available for this report."
            )
        else:
            self.proof_packet = {}
            self.proof_packet_available = False
            self.has_degraded_data = True
            self.proof_packet_status_label = (
                "Proof packet is not available for this report. This may require enterprise "
                "access or a backend endpoint not yet exposed."
            )
        self.loading = False

    def _derive_labels(self) -> None:
        merged = {**self.summary, **self.report}
        self.report_status_label = str(merged.get("status") or "Not available")
        self.generated_at_label = str(
            merged.get("generated_at") or merged.get("updated_at") or "Not available"
        )
        self.advisory_band_label = str(
            merged.get("risk_band") or merged.get("advisory_band") or "Not available"
        )
        confidence = merged.get("confidence")
        self.confidence_label = "Not available" if confidence is None else str(confidence)
        self.summary_label = str(merged.get("summary") or merged.get("message") or "Not available")
        evidence_packet = self.evidence.get("packet_id") or self.evidence.get("evidence_packet_id")
        self.evidence_label = (
            f"Evidence packet: {evidence_packet}"
            if evidence_packet
            else "Evidence unavailable. Manual review recommended."
        )
        self.has_limited_evidence = self.has_limited_evidence or not bool(self.evidence)

    def clear_error(self) -> None:
        self.error = ""

    def reset_report(self) -> None:
        self.trace_report_id = ""
        self.loading = False
        self.error = ""
        self.summary = {}
        self.report = {}
        self.evidence = {}
        self.privacy_shield = {}
        self.origin_passport = {}
        self.source_summary = {}
        self.provider_disagreement = {}
        self.utxo_hygiene = {}
        self.dust_radar = {}
        self.counterparty_lens = {}
        self.policy_facts = {}
        self.proof_packet = {}
        self.has_degraded_data = False
        self.has_provider_disagreement = False
        self.has_limited_evidence = False
        self.proof_packet_available = False
        self.failed_panels = []
        self.report_status_label = "Not available"
        self.generated_at_label = "Not available"
        self.advisory_band_label = "Not available"
        self.confidence_label = "Not available"
        self.summary_label = "Not available"
        self.evidence_label = "Evidence unavailable. Manual review recommended."
        self.proof_packet_status_label = "Proof packet is not available for this report."

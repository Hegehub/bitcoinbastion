from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.services.evidence_client import EvidenceApiClient
from bastion_ui.services.models import ApiResult


def _dict_from_result(result: ApiResult) -> dict[str, Any]:
    return result.data if result.ok and isinstance(result.data, dict) else {}


class EvidenceState(rx.State):
    evidence_report_id: str = ""
    loading: bool = False
    error: str = ""
    evidence_items: list[dict[str, Any]] = []
    proof_packet: dict[str, Any] = {}
    provider_disagreement: dict[str, Any] = {}
    degraded_sources: list[str] = []
    limitations: list[str] = [
        "Evidence is advisory-only.",
        "Evidence is not legal verification.",
        "Evidence is not Bitcoin consensus proof.",
        "Evidence may be incomplete, stale, degraded, or provider-disputed.",
    ]
    last_updated: str = "Not available"
    proof_packet_status: str = "Proof Packet unavailable until backend data is returned."
    provider_disagreement_status: str = "Provider disagreement status not available."
    degraded_evidence_visible: bool = False

    async def fetch_evidence(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        if not validation.ok:
            self.error = validation.error
            return
        self.evidence_report_id = validation.report_id
        self.loading = True
        self.error = ""
        result = await EvidenceApiClient().get_trace_evidence(self.evidence_report_id)
        if result.ok:
            data = _dict_from_result(result)
            raw_items = data.get("evidence") or data.get("items") or data.get("sources") or []
            self.evidence_items = raw_items if isinstance(raw_items, list) else []
            self.last_updated = str(
                data.get("generated_at") or data.get("updated_at") or "Not available"
            )
            self.degraded_evidence_visible = bool(result.degraded or data.get("degraded"))
        else:
            self.error = result.error or "Evidence is temporarily unavailable."
            self.degraded_evidence_visible = True
        self.loading = False

    async def fetch_proof_packet(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        if not validation.ok:
            self.error = validation.error
            return
        self.evidence_report_id = validation.report_id
        self.loading = True
        self.error = ""
        result = await EvidenceApiClient().get_proof_packet(self.evidence_report_id)
        if result.ok:
            self.proof_packet = _dict_from_result(result)
            self.proof_packet_status = (
                "Proof Packet data loaded. Review limitations before relying on it."
                if self.proof_packet
                else "Proof Packet unavailable until backend data is returned."
            )
            self.degraded_evidence_visible = bool(result.degraded)
        else:
            self.proof_packet = {}
            self.proof_packet_status = "Proof Packet unavailable. Backend data was not returned."
            self.error = result.error or "Proof Packet unavailable."
            self.degraded_evidence_visible = True
        self.loading = False

    async def fetch_provider_disagreement(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        if not validation.ok:
            self.error = validation.error
            return
        result = await EvidenceApiClient().get_provider_disagreement(validation.report_id)
        if result.ok:
            self.provider_disagreement = _dict_from_result(result)
            self.provider_disagreement_status = "Provider disagreement data loaded."
        else:
            self.provider_disagreement = {}
            self.provider_disagreement_status = (
                "Provider disagreement unavailable. Manual review recommended."
            )
            self.degraded_evidence_visible = True

    def reset_evidence(self) -> None:
        self.evidence_report_id = ""
        self.loading = False
        self.error = ""
        self.evidence_items = []
        self.proof_packet = {}
        self.provider_disagreement = {}
        self.degraded_sources = []
        self.last_updated = "Not available"
        self.proof_packet_status = "Proof Packet unavailable until backend data is returned."
        self.provider_disagreement_status = "Provider disagreement status not available."
        self.degraded_evidence_visible = False

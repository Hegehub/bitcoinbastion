from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.report_validation import validate_report_id
from bastion_ui.services.evidence_client import (
    get_proof_packet,
    get_provider_disagreement,
    get_trace_evidence,
)
from bastion_ui.services.models import ApiResult


class EvidenceState(rx.State):
    evidence_report_id: str = ""
    loading: bool = False
    error: str | None = None
    evidence_items: list[dict[str, Any]] = []
    proof_packet: dict[str, Any] | None = None
    provider_disagreement: dict[str, Any] | None = None
    degraded_sources: list[str] = []
    limitations: list[str] = []
    last_updated: str | None = None

    def _set_report_id(self, report_id: str) -> bool:
        validation = validate_report_id(report_id)
        self.evidence_report_id = validation.value if validation.ok else ""
        self.error = validation.error
        return validation.ok

    def _apply_limitations(self, result: ApiResult) -> None:
        if result.degraded:
            self.limitations.append(
                "Evidence may be incomplete, stale, degraded, or provider-disputed."
            )
        if result.error:
            self.limitations.append(result.error)

    async def fetch_evidence(self, report_id: str) -> None:
        if not self._set_report_id(report_id):
            return
        self.loading = True
        result = await get_trace_evidence(self.evidence_report_id)
        self.evidence_items = []
        if result.ok and isinstance(result.data, dict):
            items = result.data.get("items") or result.data.get("evidence_items") or []
            self.evidence_items = [item for item in items if isinstance(item, dict)]
            self.last_updated = str(
                result.data.get("generated_at") or result.data.get("updated_at") or ""
            )
        self._apply_limitations(result)
        self.loading = False

    async def fetch_proof_packet(self, report_id: str) -> None:
        if not self._set_report_id(report_id):
            return
        self.loading = True
        result = await get_proof_packet(self.evidence_report_id)
        self.proof_packet = result.data if result.ok and isinstance(result.data, dict) else None
        self._apply_limitations(result)
        if self.proof_packet is None:
            self.error = result.error or "Proof Packet unavailable."
        self.loading = False

    async def fetch_provider_disagreement(self, report_id: str) -> None:
        if not self._set_report_id(report_id):
            return
        result = await get_provider_disagreement(self.evidence_report_id)
        self.provider_disagreement = (
            result.data if result.ok and isinstance(result.data, dict) else None
        )
        if result.degraded:
            self.degraded_sources.append(
                "Provider disagreement or stale evidence state is visible."
            )
        self._apply_limitations(result)

    def reset(self) -> None:
        self.evidence_report_id = ""
        self.loading = False
        self.error = None
        self.evidence_items = []
        self.proof_packet = None
        self.provider_disagreement = None
        self.degraded_sources = []
        self.limitations = []
        self.last_updated = None

from __future__ import annotations

from typing import Any

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt14 import (
    TraceEvidenceViewModel,
    TraceProofPacketViewModel,
    adapt_trace_proof_packet,
)
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    GetCurrentTraceProofPacketRequest,
    GetHistoricalTraceProofPacketRequest,
    get_current_trace_proof_packet,
    get_historical_trace_proof_packet,
)


class TraceProofPacketState(rx.State):
    """Request owner; canonical packet membership remains backend-owned."""

    packet_report_id: str = ""
    packet_snapshot_id: str = ""
    current_packet: TraceProofPacketViewModel | None = None
    historical_packet: TraceProofPacketViewModel | None = None
    selected_evidence: TraceEvidenceViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    provenance: str = ProvenanceState.LIVE.value
    generation: int = 0

    @rx.var
    def active_packet(self) -> TraceProofPacketViewModel | None:
        return self.historical_packet if self.packet_snapshot_id else self.current_packet

    async def load_route(self) -> None:
        validation = validate_report_id(self.router.page.params.get("report_id", ""))
        if not validation.ok:
            self.safe_error = validation.error
            self.lifecycle = LifecycleStatus.VALIDATION_ERROR.value
            return
        requested_snapshot = self.router.page.params.get("snapshot_id", "").strip()
        if requested_snapshot and not requested_snapshot.startswith("trace_snapshot:"):
            self.safe_error = "Historical snapshot identity is invalid."
            self.lifecycle = LifecycleStatus.VALIDATION_ERROR.value
            return
        self.packet_report_id = validation.report_id
        self.packet_snapshot_id = requested_snapshot
        # Route identity changes invalidate rendered packet/detail state immediately;
        # stale A/B content must never remain visible while the exact read is in flight.
        self.selected_evidence = None
        if requested_snapshot:
            self.historical_packet = None
        else:
            self.current_packet = None
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        try:
            config = get_config()
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                transport = HttpTransport(client, timeout_seconds=config.request_timeout_seconds)
                if requested_snapshot:
                    historical_result = await get_historical_trace_proof_packet(
                        transport,
                        GetHistoricalTraceProofPacketRequest(
                            report_id=int(self.packet_report_id), snapshot_id=requested_snapshot
                        ),
                    )
                    packet = adapt_trace_proof_packet(historical_result.root.data)
                else:
                    current_result = await get_current_trace_proof_packet(
                        transport,
                        GetCurrentTraceProofPacketRequest(
                            report_id=int(self.packet_report_id)
                        ),
                    )
                    packet = adapt_trace_proof_packet(current_result.root.data)
            if token != self.generation or requested_snapshot != self.packet_snapshot_id:
                return
            if requested_snapshot:
                self.historical_packet = packet
            else:
                self.current_packet = packet
            self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            if token == self.generation:
                status, error = project_transport_error(exc)
                self.safe_error = error.summary
                self.lifecycle = status.value

    def select_evidence_item(self, evidence: TraceEvidenceViewModel) -> None:
        self.selected_evidence = evidence

    def close_evidence_item(self) -> Any:
        evidence_id = self.selected_evidence.evidence_id if self.selected_evidence else ""
        self.selected_evidence = None
        return rx.call_script(
            "document.getElementById('evidence-trigger-"
            + evidence_id
            + "')?.focus()"
        )

    def invalidate(self) -> None:
        self.generation += 1
        self.lifecycle = LifecycleStatus.IDLE.value
        self.selected_evidence = None

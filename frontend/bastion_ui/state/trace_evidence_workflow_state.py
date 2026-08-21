from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt15 import (
    EvidenceExportViewModel,
    EvidenceLineageViewModel,
    EvidenceReplayViewModel,
    EvidenceVerificationViewModel,
    adapt_evidence_export,
    adapt_evidence_lineage,
    adapt_evidence_replay,
    adapt_evidence_verification,
)
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    ExportTraceEvidenceRequest,
    GetTraceEvidenceLineageRequest,
    ReplayTraceEvidenceRequest,
    VerifyTraceEvidenceIdentityRequest,
    export_trace_evidence,
    get_trace_evidence_lineage,
    replay_trace_evidence,
    verify_trace_evidence_identity,
)


class TraceEvidenceWorkflowState(rx.State):
    """Prompt-15 action owner; original Evidence remains in Prompt-14 State."""

    workflow_report_id: str = ""
    workflow_snapshot_id: str = ""
    workflow_evidence_id: str = ""
    historical: bool = False
    lineage: EvidenceLineageViewModel | None = None
    replay: EvidenceReplayViewModel | None = None
    verification: EvidenceVerificationViewModel | None = None
    export: EvidenceExportViewModel | None = None
    lineage_lifecycle: str = LifecycleStatus.IDLE.value
    replay_lifecycle: str = LifecycleStatus.IDLE.value
    verification_lifecycle: str = LifecycleStatus.IDLE.value
    export_lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    copy_status: str = ""
    generation: int = 0

    def prepare(
        self, report_id: str, snapshot_id: str, evidence_id: str, historical: bool
    ) -> None:
        self.generation += 1
        self.workflow_report_id = report_id
        self.workflow_snapshot_id = snapshot_id
        self.workflow_evidence_id = evidence_id
        self.historical = historical
        self.lineage = None
        self.replay = None
        self.verification = None
        self.export = None
        self.lineage_lifecycle = LifecycleStatus.IDLE.value
        self.replay_lifecycle = LifecycleStatus.IDLE.value
        self.verification_lifecycle = LifecycleStatus.IDLE.value
        self.export_lifecycle = LifecycleStatus.IDLE.value
        self.safe_error = ""
        self.copy_status = ""

    def _context(self) -> tuple[int, str, str, bool, int]:
        return (
            int(self.workflow_report_id),
            self.workflow_snapshot_id,
            self.workflow_evidence_id,
            self.historical,
            self.generation,
        )

    def _still_current(self, evidence_id: str, snapshot_id: str, token: int) -> bool:
        return (
            token == self.generation
            and evidence_id == self.workflow_evidence_id
            and snapshot_id == self.workflow_snapshot_id
        )

    async def load_lineage(self) -> None:
        report_id, snapshot_id, evidence_id, historical, token = self._context()
        self.lineage_lifecycle = LifecycleStatus.LOADING.value
        try:
            async with self._transport() as transport:
                response = await get_trace_evidence_lineage(
                    transport,
                    GetTraceEvidenceLineageRequest(
                        report_id=report_id,
                        evidence_id=evidence_id,
                        snapshot_id=snapshot_id,
                        historical=historical,
                    ),
                )
            if self._still_current(evidence_id, snapshot_id, token):
                self.lineage = adapt_evidence_lineage(response.root.data)
                self.lineage_lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            self._set_error(exc, "lineage_lifecycle", token)

    async def run_replay(self) -> None:
        report_id, snapshot_id, evidence_id, historical, token = self._context()
        self.replay_lifecycle = LifecycleStatus.LOADING.value
        try:
            async with self._transport() as transport:
                response = await replay_trace_evidence(
                    transport,
                    ReplayTraceEvidenceRequest(
                        report_id=report_id,
                        evidence_id=evidence_id,
                        snapshot_id=snapshot_id,
                        historical=historical,
                    ),
                )
            if self._still_current(evidence_id, snapshot_id, token):
                self.replay = adapt_evidence_replay(response.root.data)
                self.replay_lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            self._set_error(exc, "replay_lifecycle", token)

    async def run_verification(self) -> None:
        report_id, snapshot_id, evidence_id, historical, token = self._context()
        self.verification_lifecycle = LifecycleStatus.LOADING.value
        try:
            async with self._transport() as transport:
                response = await verify_trace_evidence_identity(
                    transport,
                    VerifyTraceEvidenceIdentityRequest(
                        report_id=report_id,
                        evidence_id=evidence_id,
                        snapshot_id=snapshot_id,
                        historical=historical,
                    ),
                )
            if self._still_current(evidence_id, snapshot_id, token):
                self.verification = adapt_evidence_verification(response.root.data)
                self.verification_lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            self._set_error(exc, "verification_lifecycle", token)

    async def export_evidence(self) -> Any:
        report_id, snapshot_id, evidence_id, historical, token = self._context()
        self.export_lifecycle = LifecycleStatus.LOADING.value
        try:
            async with self._transport() as transport:
                response = await export_trace_evidence(
                    transport,
                    ExportTraceEvidenceRequest(
                        report_id=report_id,
                        evidence_id=evidence_id,
                        snapshot_id=snapshot_id,
                        historical=historical,
                    ),
                )
            if not self._still_current(evidence_id, snapshot_id, token):
                return None
            self.export = adapt_evidence_export(response.root.data)
            self.export_lifecycle = LifecycleStatus.SUCCESS.value
            return rx.download(
                data=response.root.data.content, filename=response.root.data.filename
            )
        except SafeTransportError as exc:
            self._set_error(exc, "export_lifecycle", token)
            return None

    def mark_copied(self) -> None:
        self.copy_status = "Safe Evidence ID copied."

    def invalidate(self) -> None:
        self.generation += 1
        self.workflow_evidence_id = ""
        self.lineage = None
        self.replay = None
        self.verification = None
        self.export = None
        self.copy_status = ""

    @asynccontextmanager
    async def _transport(self) -> AsyncIterator[HttpTransport]:
        config = get_config()
        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            yield HttpTransport(client, timeout_seconds=config.request_timeout_seconds)

    def _set_error(self, exc: SafeTransportError, lifecycle: str, token: int) -> None:
        if token != self.generation:
            return
        status, error = project_transport_error(exc)
        self.safe_error = error.summary
        setattr(self, lifecycle, status.value)

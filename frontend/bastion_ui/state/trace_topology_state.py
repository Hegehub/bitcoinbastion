from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt13 import (
    TraceDisagreementCollectionViewModel,
    TraceHistoryIndexItemViewModel,
    TraceTopologyNodeViewModel,
    TraceTopologyRelationshipViewModel,
    TraceTopologyViewModel,
    adapt_trace_disagreements,
    adapt_trace_graph,
    adapt_trace_history,
)
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.security.report_id_validation import validate_report_id
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    GetCurrentTraceDisagreementRequest,
    GetExactTraceGraphSnapshotRequest,
    GetHistoricalTraceDisagreementRequest,
    GetTraceGraphHistoryApiV1TraceReportReportIdGraphHistoryGetRequest,
    get_current_trace_disagreement,
    get_exact_trace_graph_snapshot,
    get_historical_trace_disagreement,
    get_trace_graph_history_api_v1_trace_report__report_id__graph_history_get,
)


class TraceTopologyState(rx.State):
    """Current topology owner; generated transport objects end at Feature-54."""

    current_report_id: str = ""
    topology: TraceTopologyViewModel | None = None
    history: tuple[TraceHistoryIndexItemViewModel, ...] = ()
    disagreement: TraceDisagreementCollectionViewModel | None = None
    selected_node: TraceTopologyNodeViewModel | None = None
    selected_relationship: TraceTopologyRelationshipViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    provenance: str = ProvenanceState.LIVE.value
    generation: int = 0

    async def load_route(self) -> None:
        validation = validate_report_id(self.router.page.params.get("report_id", ""))
        if not validation.ok:
            self.safe_error = validation.error
            self.lifecycle = LifecycleStatus.VALIDATION_ERROR.value
            return
        self.current_report_id = validation.report_id
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        try:
            config = get_config()
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                transport = HttpTransport(client, timeout_seconds=config.request_timeout_seconds)
                report_id = int(self.current_report_id)
                history_result = (
                    await get_trace_graph_history_api_v1_trace_report__report_id__graph_history_get(
                        transport,
                        GetTraceGraphHistoryApiV1TraceReportReportIdGraphHistoryGetRequest(
                            report_id=report_id
                        ),
                    )
                )
                history = adapt_trace_history(history_result.root.data)
                if token != self.generation:
                    return
                self.history = history
                if not history:
                    self.lifecycle = LifecycleStatus.EMPTY.value
                    return
                latest_id = history[-1].snapshot_id
                graph_result = await get_exact_trace_graph_snapshot(
                    transport,
                    GetExactTraceGraphSnapshotRequest(report_id=report_id, snapshot_id=latest_id),
                )
                disagreement_result = await get_current_trace_disagreement(
                    transport, GetCurrentTraceDisagreementRequest(report_id=report_id)
                )
                if token != self.generation:
                    return
                self.topology = adapt_trace_graph(graph_result.root.data)
                self.disagreement = adapt_trace_disagreements(disagreement_result.root.data)
                self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            if token == self.generation:
                status, error = project_transport_error(exc)
                self.safe_error = error.summary
                self.lifecycle = status.value

    def select_node(self, node: TraceTopologyNodeViewModel) -> None:
        self.selected_node = node
        self.selected_relationship = None

    def select_relationship(self, relationship: TraceTopologyRelationshipViewModel) -> None:
        self.selected_relationship = relationship
        self.selected_node = None

    def invalidate(self) -> None:
        self.generation += 1
        self.lifecycle = LifecycleStatus.IDLE.value
        self.selected_node = None
        self.selected_relationship = None


class TraceHistoryState(rx.State):
    """Exact historical state isolated from the current topology owner."""

    historical_report_id: str = ""
    selected_snapshot_id: str = ""
    topology: TraceTopologyViewModel | None = None
    disagreement: TraceDisagreementCollectionViewModel | None = None
    selected_node: TraceTopologyNodeViewModel | None = None
    selected_relationship: TraceTopologyRelationshipViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    provenance: str = ProvenanceState.LIVE.value
    generation: int = 0

    async def load_route(self) -> None:
        validation = validate_report_id(self.router.page.params.get("report_id", ""))
        snapshot_id = self.router.page.params.get("snapshot_id", "").strip()
        if not validation.ok or not snapshot_id.startswith("trace_snapshot:"):
            self.safe_error = validation.error or "Historical snapshot identity is invalid."
            self.lifecycle = LifecycleStatus.VALIDATION_ERROR.value
            return
        self.historical_report_id = validation.report_id
        self.selected_snapshot_id = snapshot_id
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        try:
            config = get_config()
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                transport = HttpTransport(client, timeout_seconds=config.request_timeout_seconds)
                request = GetExactTraceGraphSnapshotRequest(
                    report_id=int(self.historical_report_id), snapshot_id=snapshot_id
                )
                graph_result = await get_exact_trace_graph_snapshot(transport, request)
                disagreement_result = await get_historical_trace_disagreement(
                    transport,
                    GetHistoricalTraceDisagreementRequest(
                        report_id=int(self.historical_report_id), snapshot_id=snapshot_id
                    ),
                )
                if token != self.generation or snapshot_id != self.selected_snapshot_id:
                    return
                self.topology = adapt_trace_graph(graph_result.root.data)
                self.disagreement = adapt_trace_disagreements(disagreement_result.root.data)
                self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as exc:
            if token == self.generation:
                status, error = project_transport_error(exc)
                self.safe_error = error.summary
                self.lifecycle = status.value

    def select_node(self, node: TraceTopologyNodeViewModel) -> None:
        self.selected_node = node
        self.selected_relationship = None

    def select_relationship(self, relationship: TraceTopologyRelationshipViewModel) -> None:
        self.selected_relationship = relationship
        self.selected_node = None

    def invalidate(self) -> None:
        self.generation += 1
        self.lifecycle = LifecycleStatus.IDLE.value
        self.selected_snapshot_id = ""
        self.selected_node = None
        self.selected_relationship = None

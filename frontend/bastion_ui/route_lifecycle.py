"""Route transition coordination over existing Stage-2/3/4 lifecycle owners."""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from bastion_ui.state.operations_state import (
    HealthState,
    IncidentsState,
    OperationsSLOState,
    ProvidersState,
    StorageState,
)
from bastion_ui.state.prompt2_status_state import Prompt2StatusState
from bastion_ui.state.prompt9_state import JobsState, MarketOverviewState, MarketSignalsState
from bastion_ui.state.prompt10_state import MarketHistoryState
from bastion_ui.state.prompt11_state import MarketSimilarityState
from bastion_ui.state.security_shell_state import SecurityShellState
from bastion_ui.state.trace_report_state import TraceReportState
from bastion_ui.state.websocket_lab_state import WebSocketLabState
from bastion_ui.topology import ROUTE_BY_ID


@dataclass(frozen=True)
class TransitionActions:
    invalidate_http: bool
    invalidate_security: bool
    disconnect_websocket: bool
    refresh_security: bool
    connect_websocket: bool


def transition_actions(previous: str | None, current: str) -> TransitionActions:
    route = ROUTE_BY_ID[current]
    changed = previous != current
    return TransitionActions(
        invalidate_http=changed,
        invalidate_security=changed,
        disconnect_websocket=changed,
        refresh_security=route.security_requirement_id in {"access.me", "operator"},
        connect_websocket=bool(route.ws_families),
    )


class RouteLifecycleState(rx.State):
    """Coordinates route ownership; it does not duplicate transport managers."""

    active_route_id: str = ""
    request_generation: int = 0

    def enter(self, route_id: str) -> list[object]:
        actions = transition_actions(self.active_route_id or None, route_id)
        self.active_route_id = route_id
        events: list[object] = []
        if actions.invalidate_http:
            self.request_generation += 1
            events.append(Prompt2StatusState.cancel_status)
            events.append(TraceReportState.invalidate_route)
            events.extend(
                (
                    HealthState.invalidate,
                    ProvidersState.invalidate,
                    StorageState.invalidate,
                    IncidentsState.invalidate,
                    OperationsSLOState.invalidate,
                    MarketHistoryState.invalidate,
                    MarketSimilarityState.invalidate,
                )
            )
        if actions.invalidate_security:
            events.append(SecurityShellState.invalidate)
        if actions.disconnect_websocket:
            events.append(WebSocketLabState.disconnect)
        if actions.refresh_security:
            events.append(SecurityShellState.refresh_posture)
        if actions.connect_websocket:
            events.append(WebSocketLabState.connect_provider_health)
        if route_id in {"trace.report", "trace.proof_packet"}:
            events.append(TraceReportState.validate_current_route)
        if route_id == "trace.report":
            events.append(TraceReportState.load_trace_report)
        if route_id in {"overview.home", "operations"}:
            events.extend((HealthState.load, ProvidersState.load, StorageState.load))
        elif route_id == "operations.health":
            events.append(HealthState.load)
        elif route_id == "operations.providers":
            events.append(ProvidersState.load)
        elif route_id == "operations.storage":
            events.append(StorageState.load)
        elif route_id == "operations.incidents":
            events.append(IncidentsState.load)
        elif route_id == "operations.slo":
            events.append(OperationsSLOState.load)
        elif route_id == "operations.jobs":
            events.append(JobsState.load)
        elif route_id == "market.home":
            events.append(MarketOverviewState.load)
        elif route_id == "market.signals":
            events.append(MarketSignalsState.load)
        elif route_id == "market.timeline":
            events.append(MarketHistoryState.load_timeline)
        elif route_id == "market.similarity":
            events.append(MarketSimilarityState.load)
        elif route_id == "market.time_machine":
            events.append(MarketHistoryState.load_attributions)
        elif route_id == "market.replay":
            events.append(MarketHistoryState.load_replay_route)
        elif route_id == "market.narratives":
            events.append(MarketHistoryState.load_narratives)
        elif route_id == "market.sources":
            events.append(MarketHistoryState.load_sources)
        return events

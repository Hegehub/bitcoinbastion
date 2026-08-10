from __future__ import annotations

from datetime import UTC, datetime

import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.realtime.adapters import adapt_connection_accepted
from bastion_ui.realtime.contracts import SystemFrame
from bastion_ui.realtime.degraded_lab import run_scenario
from bastion_ui.realtime.models import StreamStatusViewModel
from bastion_ui.realtime.transport import ConnectionStatus, WebSocketTransport


class WebSocketLabState(rx.State):
    view_model: StreamStatusViewModel | None = None
    connection_status: str = ConnectionStatus.DISCONNECTED.value
    safe_error: str = ""
    request_generation: int = 0

    @rx.var
    def stream(self) -> str:
        return self.view_model.stream if self.view_model else "Not connected"

    @rx.var
    def message(self) -> str:
        return self.view_model.message if self.view_model else "No authoritative frame received"

    @rx.var
    def wire_version(self) -> str:
        return str(self.view_model.wire_version) if self.view_model else "Unavailable"

    @rx.var
    def provenance(self) -> str:
        return (
            self.view_model.provenance.state.value
            if self.view_model
            else ProvenanceState.UNAVAILABLE.value
        )

    async def connect_provider_health(self) -> None:
        self.request_generation += 1
        token = self.request_generation
        self.connection_status = ConnectionStatus.CONNECTING.value
        self.safe_error = ""
        transport = WebSocketTransport()
        base = get_config().api_base_url.replace("https://", "wss://").replace("http://", "ws://")
        try:
            frame = await transport.receive_first(
                f"{base}/api/v1/ws/provider-health?limit_payload=true"
            )
            if token != self.request_generation or not isinstance(frame, SystemFrame):
                return
            self.view_model = adapt_connection_accepted(
                frame,
                Provenance(
                    state=ProvenanceState.LIVE,
                    source_label="Provider health WebSocket",
                    observed_at=datetime.now(UTC),
                ),
            )
            self.connection_status = transport.status.value
        except Exception:
            if token == self.request_generation:
                self.connection_status = ConnectionStatus.FAILED.value
                self.safe_error = (
                    "The provider-health stream is unavailable. Demo data was not substituted."
                )

    def disconnect(self) -> None:
        self.request_generation += 1
        self.connection_status = ConnectionStatus.DISCONNECTED.value

    def demo_unsupported_version(self) -> None:
        result = run_scenario("unsupported-version")
        self.view_model = None
        self.connection_status = result.status.value
        self.safe_error = "DEMO_FIXTURE: unsupported wire version rejected safely."

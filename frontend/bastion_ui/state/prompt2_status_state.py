from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.overview.adapters import adapt_public_status
from bastion_ui.domain.overview.models import PublicStatusViewModel
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    PublicStatusApiV1PublicStatusGetRequest,
    public_status_api_v1_public_status_get,
)


class Prompt2StatusState(rx.State):
    """Page-local State: safe view model only, never a raw transport DTO."""

    view_model: PublicStatusViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    request_generation: int = 0

    @rx.var
    def platform_status(self) -> str:
        return self.view_model.platform_status if self.view_model else "Not loaded"

    @rx.var
    def trace_status(self) -> str:
        return self.view_model.trace_status if self.view_model else "Not loaded"

    @rx.var
    def last_update(self) -> str:
        return self.view_model.last_update.isoformat() if self.view_model else "Not available"

    @rx.var
    def provenance_state(self) -> str:
        return self.view_model.provenance.state.value if self.view_model else "UNAVAILABLE"

    @rx.var
    def provenance_source(self) -> str:
        return self.view_model.provenance.source_label if self.view_model else "No valid source"

    @rx.var
    def provenance_details(self) -> str:
        if not self.view_model:
            return "No current runtime result is available."
        return self.view_model.provenance.limitation or "No additional limitation supplied."

    async def load_status(self) -> None:
        self.request_generation += 1
        token = self.request_generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await public_status_api_v1_public_status_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    PublicStatusApiV1PublicStatusGetRequest(),
                )
            if token != self.request_generation:
                return
            view_model = adapt_public_status(response)
            self.view_model = view_model
            self.lifecycle = (
                LifecycleStatus.EMPTY.value
                if not view_model.modules
                else LifecycleStatus.SUCCESS.value
            )
        except SafeTransportError as error:
            if token != self.request_generation:
                return
            status, safe_error = project_transport_error(error)
            self.lifecycle = status.value
            self.safe_error = safe_error.summary

    def cancel_status(self) -> None:
        self.request_generation += 1
        if self.lifecycle == LifecycleStatus.LOADING.value:
            self.lifecycle = LifecycleStatus.IDLE.value
        self.safe_error = ""

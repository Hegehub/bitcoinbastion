from __future__ import annotations

from datetime import UTC, datetime

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.access.security import SecurityPostureViewModel, adapt_access_me
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    GetMeApiV1AccessMeGetRequest,
    get_me_api_v1_access_me_get,
)


class SecurityShellState(rx.State):
    """Fail-closed, browser-safe posture state; never stores proof/session material."""

    posture: SecurityPostureViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    denial_heading: str = "Checking Access"
    denial_detail: str = "Protected content remains hidden until the backend confirms Access."
    request_generation: int = 0

    @rx.var
    def protected_visible(self) -> bool:
        return bool(self.posture and self.posture.session.value == "ACTIVE")

    @rx.var
    def operator_visible(self) -> bool:
        return bool(
            self.posture
            and self.posture.session.value == "ACTIVE"
            and "operator" in self.posture.capabilities
        )

    async def refresh_posture(self) -> None:
        self.request_generation += 1
        token = self.request_generation
        self.posture = None
        self.lifecycle = LifecycleStatus.LOADING.value
        self.denial_heading = "Checking Access"
        try:
            config = get_config()
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await get_me_api_v1_access_me_get(
                    HttpTransport(client), GetMeApiV1AccessMeGetRequest()
                )
            if token != self.request_generation:
                return
            self.posture = adapt_access_me(
                response,
                Provenance(
                    state=ProvenanceState.LIVE,
                    source_label="Proof-of-Access session endpoint",
                    observed_at=datetime.now(UTC),
                ),
            )
            self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as error:
            if token != self.request_generation:
                return
            status, safe = project_transport_error(error)
            self.lifecycle = status.value
            self.denial_heading = "Access required"
            self.denial_detail = safe.summary

    def invalidate(self) -> None:
        self.request_generation += 1
        self.posture = None
        self.lifecycle = LifecycleStatus.IDLE.value

from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt9 import (
    JobsViewModel,
    MarketOverviewViewModel,
    MarketSignalsViewModel,
    adapt_jobs,
    adapt_market_overview,
    adapt_market_signals,
)
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    JobsApiV1OperationsJobsGetRequest,
    MarketCurrentOverviewRequest,
    TopSignalsApiV1SignalsTopGetRequest,
    jobs_api_v1_operations_jobs_get,
    market_current_overview,
    top_signals_api_v1_signals_top_get,
)


class JobsState(rx.State):
    value: JobsViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await jobs_api_v1_operations_jobs_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    JobsApiV1OperationsJobsGetRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_jobs(response)
            self.lifecycle = (
                LifecycleStatus.SUCCESS.value if self.value.jobs else LifecycleStatus.EMPTY.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class MarketOverviewState(rx.State):
    value: MarketOverviewViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await market_current_overview(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    MarketCurrentOverviewRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_market_overview(response)
            self.lifecycle = (
                LifecycleStatus.SUCCESS.value
                if self.value.price_usd is not None
                else LifecycleStatus.DEGRADED.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class MarketSignalsState(rx.State):
    value: MarketSignalsViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await top_signals_api_v1_signals_top_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    TopSignalsApiV1SignalsTopGetRequest(limit=25, offset=0, horizon=None),
                )
            if token != self.generation:
                return
            self.value = adapt_market_signals(response)
            self.lifecycle = (
                LifecycleStatus.SUCCESS.value if self.value.signals else LifecycleStatus.EMPTY.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1

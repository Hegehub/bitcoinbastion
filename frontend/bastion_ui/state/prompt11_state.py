from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt11 import SimilarityReportViewModel, adapt_similarity
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    MarketSimilarityReportRequest,
    market_similarity_report,
)


class MarketSimilarityState(rx.State):
    report: SimilarityReportViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self, event_id: int = 1) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await market_similarity_report(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    MarketSimilarityReportRequest(event_id=event_id, limit=10),
                )
            if token == self.generation:
                self.report = adapt_similarity(response)
                self.lifecycle = (
                    LifecycleStatus.SUCCESS.value
                    if self.report.results
                    else LifecycleStatus.EMPTY.value
                )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1

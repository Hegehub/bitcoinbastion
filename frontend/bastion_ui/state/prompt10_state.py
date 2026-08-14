from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.prompt10 import (
    AttributionViewModel,
    NarrativeViewModel,
    ReplayViewModel,
    SourceViewModel,
    TimelineItemViewModel,
    TimelineViewModel,
    adapt_attributions,
    adapt_narratives,
    adapt_replay,
    adapt_sources,
    adapt_timeline,
)
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    MarketHistoryAttributionsRequest,
    MarketHistoryNarrativesRequest,
    MarketHistoryReplayEventRequest,
    MarketHistorySourcesRequest,
    MarketHistoryTimelineRequest,
    market_history_attributions,
    market_history_narratives,
    market_history_replay_event,
    market_history_sources,
    market_history_timeline,
)


class MarketHistoryState(rx.State):
    timeline: TimelineViewModel | None = None
    timeline_items: tuple[TimelineItemViewModel, ...] = ()
    timeline_ordering: str = "occurred_at_desc,event_id_desc"
    replay: ReplayViewModel | None = None
    attributions: tuple[AttributionViewModel, ...] = ()
    narratives: tuple[NarrativeViewModel, ...] = ()
    sources: tuple[SourceViewModel, ...] = ()
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    provenance: str = ProvenanceState.LIVE.value
    generation: int = 0

    async def _request(self, request_name: str, event_id: int | None = None) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                transport = HttpTransport(client, timeout_seconds=config.request_timeout_seconds)
                if request_name == "timeline":
                    self.timeline = adapt_timeline(
                        await market_history_timeline(
                            transport, MarketHistoryTimelineRequest(limit=50, before_sequence=None)
                        )
                    )
                    self.timeline_items = self.timeline.items
                    self.timeline_ordering = self.timeline.ordering
                elif request_name == "replay" and event_id is not None:
                    self.replay = adapt_replay(
                        await market_history_replay_event(
                            transport, MarketHistoryReplayEventRequest(event_id=event_id)
                        )
                    )
                elif request_name == "attributions":
                    self.attributions = adapt_attributions(
                        await market_history_attributions(
                            transport, MarketHistoryAttributionsRequest(limit=50)
                        )
                    )
                elif request_name == "narratives":
                    self.narratives = adapt_narratives(
                        await market_history_narratives(
                            transport, MarketHistoryNarrativesRequest(limit=50)
                        )
                    )
                elif request_name == "sources":
                    self.sources = adapt_sources(
                        await market_history_sources(
                            transport, MarketHistorySourcesRequest(limit=50)
                        )
                    )
            if token == self.generation:
                timeline_empty = self.timeline is None or not self.timeline.items
                collection_empty = (
                    (request_name == "timeline" and timeline_empty)
                    or (request_name == "attributions" and not self.attributions)
                    or (request_name == "narratives" and not self.narratives)
                    or (request_name == "sources" and not self.sources)
                )
                self.lifecycle = (
                    LifecycleStatus.EMPTY.value
                    if collection_empty
                    else LifecycleStatus.SUCCESS.value
                )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    async def load_timeline(self) -> None:
        await self._request("timeline")

    async def load_attributions(self) -> None:
        await self._request("attributions")

    async def load_narratives(self) -> None:
        await self._request("narratives")

    async def load_sources(self) -> None:
        await self._request("sources")

    async def load_replay(self, event_id: int) -> None:
        await self._request("replay", event_id)

    async def load_replay_route(self) -> None:
        raw = self.router.page.params.get("event_id", "")
        if raw.isdigit():
            await self._request("replay", int(raw))
        else:
            self.lifecycle = LifecycleStatus.ERROR.value
            self.safe_error = "Historical replay identity is invalid."

    def invalidate(self) -> None:
        self.generation += 1

import pytest

from app.events.registry import EVENT_REGISTRY
from app.events.types import BastionEventType
from app.services.events.websocket_filters import (
    SPECIALIZED_STREAM_EVENT_TYPES,
    event_type_to_topic,
    should_deliver,
    stream_event_types,
    stream_topics,
)


@pytest.mark.parametrize(
    ("stream", "expected"),
    [
        (
            "signals",
            {
                "signal.created",
                "signal.published",
                "signal.suppressed",
                "signal.operator_review_required",
                "signal.confidence_changed",
            },
        ),
        (
            "news",
            {
                "news.article.created",
                "news.article.scored",
                "news.event.created",
                "news.event.high_impact",
            },
        ),
        (
            "onchain",
            {
                "onchain.large_transfer",
                "onchain.watchlist_hit",
                "onchain.fee_spike",
                "onchain.mempool_pressure",
            },
        ),
        (
            "market",
            {
                "market.price_tick",
                "market.candle_closed",
                "market.regime.changed",
                "market.candle.attributed",
                "market.provider_confidence_changed",
            },
        ),
        (
            "trace",
            {
                "trace.report.created",
                "trace.report.progress",
                "trace.risk_band.changed",
                "trace.batch.completed",
                "trace.source_disagreement.updated",
                "trace.evidence.updated",
            },
        ),
        (
            "treasury",
            {
                "treasury.request.created",
                "treasury.approval.required",
                "treasury.request.approved",
                "treasury.request.rejected",
                "treasury.policy.failed",
                "treasury.psbt_status.changed",
            },
        ),
        (
            "provider-health",
            {
                "provider.degraded",
                "provider.recovered",
                "provider.stale",
                "pipeline.lag.high",
                "job.failed",
                "job.recovered",
            },
        ),
        (
            "intelligence-timeline",
            {
                "intelligence.timeline.item.created",
                "intelligence.timeline.item.updated",
                "market.candle.attributed",
                "news.event.high_impact",
                "signal.published",
                "evidence.packet.created",
            },
        ),
    ],
)
def test_specialized_stream_event_mappings(stream: str, expected: set[str]) -> None:
    assert stream_event_types(stream) == expected


@pytest.mark.parametrize("stream", sorted(SPECIALIZED_STREAM_EVENT_TYPES))
def test_specialized_stream_event_types_are_registered(stream: str) -> None:
    registered = {event.value for event in BastionEventType}
    assert stream_event_types(stream) <= registered
    assert all(
        BastionEventType(event_type) in EVENT_REGISTRY for event_type in stream_event_types(stream)
    )


def test_stream_topics_are_derived_from_event_types() -> None:
    assert stream_topics("signals") == {"signals"}
    assert stream_topics("provider-health") == {"provider-health", "observability"}
    assert stream_topics("intelligence-timeline") == {
        "intelligence-timeline",
        "market",
        "news",
        "signals",
        "evidence",
    }


def test_specialized_filter_rejects_non_allowed_event_type() -> None:
    signal_events = stream_event_types("signals")
    assert "trace.report.created" not in signal_events
    assert should_deliver("signal.published", stream_topics("signals"))
    assert event_type_to_topic("something.unknown") == "observability"

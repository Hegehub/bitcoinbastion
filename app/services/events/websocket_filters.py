from __future__ import annotations

from types import MappingProxyType

SUPPORTED_TOPICS: set[str] = {
    "signals",
    "trace",
    "market",
    "news",
    "onchain",
    "treasury",
    "policy",
    "wallet",
    "evidence",
    "provider-health",
    "observability",
    "intelligence-timeline",
}

_EVENT_PREFIX_TOPICS = {
    "signal": "signals",
    "trace": "trace",
    "market": "market",
    "news": "news",
    "onchain": "onchain",
    "treasury": "treasury",
    "policy": "policy",
    "wallet": "wallet",
    "evidence": "evidence",
    "provider": "provider-health",
    "pipeline": "observability",
    "job": "observability",
    "system": "observability",
    "webhook": "observability",
}

_EVENT_TYPE_OVERRIDES = {
    "intelligence.timeline.updated": "intelligence-timeline",
    "intelligence.timeline.item.created": "intelligence-timeline",
    "intelligence.timeline.item.updated": "intelligence-timeline",
}

_SPECIALIZED_STREAM_EVENT_TYPES: dict[str, frozenset[str]] = {
    "signals": frozenset(
        {
            "signal.created",
            "signal.published",
            "signal.suppressed",
            "signal.operator_review_required",
            "signal.confidence_changed",
        }
    ),
    "news": frozenset(
        {
            "news.article.created",
            "news.article.scored",
            "news.event.created",
            "news.event.high_impact",
        }
    ),
    "onchain": frozenset(
        {
            "onchain.large_transfer",
            "onchain.watchlist_hit",
            "onchain.fee_spike",
            "onchain.mempool_pressure",
        }
    ),
    "market": frozenset(
        {
            "market.price_tick",
            "market.candle_closed",
            "market.regime.changed",
            "market.candle.attributed",
            "market.provider_confidence_changed",
        }
    ),
    "trace": frozenset(
        {
            "trace.report.created",
            "trace.report.progress",
            "trace.risk_band.changed",
            "trace.batch.completed",
            "trace.source_disagreement.updated",
            "trace.evidence.updated",
        }
    ),
    "treasury": frozenset(
        {
            "treasury.request.created",
            "treasury.approval.required",
            "treasury.request.approved",
            "treasury.request.rejected",
            "treasury.policy.failed",
            "treasury.psbt_status.changed",
        }
    ),
    "provider-health": frozenset(
        {
            "provider.degraded",
            "provider.recovered",
            "provider.stale",
            "pipeline.lag.high",
            "job.failed",
            "job.recovered",
        }
    ),
    "intelligence-timeline": frozenset(
        {
            "intelligence.timeline.item.created",
            "intelligence.timeline.item.updated",
            "market.candle.attributed",
            "news.event.high_impact",
            "signal.published",
            "evidence.packet.created",
        }
    ),
}

SPECIALIZED_STREAM_EVENT_TYPES = MappingProxyType(_SPECIALIZED_STREAM_EVENT_TYPES)
SPECIALIZED_STREAMS = frozenset(_SPECIALIZED_STREAM_EVENT_TYPES)


class WebSocketTopicError(ValueError):
    pass


def parse_topics(raw: str | None) -> set[str]:
    if raw is None or not raw.strip():
        return set(SUPPORTED_TOPICS)
    topics = {item.strip().casefold() for item in raw.split(",") if item.strip()}
    if not topics:
        return set(SUPPORTED_TOPICS)
    unknown = topics - SUPPORTED_TOPICS
    if unknown:
        raise WebSocketTopicError("One or more requested topics are not supported.")
    return topics


def event_type_to_topic(event_type: str) -> str:
    normalized = (event_type or "").strip().casefold()
    if normalized in _EVENT_TYPE_OVERRIDES:
        return _EVENT_TYPE_OVERRIDES[normalized]
    prefix = normalized.split(".", 1)[0]
    return _EVENT_PREFIX_TOPICS.get(prefix, "observability")


def should_deliver(event_type: str, subscribed_topics: set[str]) -> bool:
    return event_type_to_topic(event_type) in subscribed_topics


def stream_event_types(stream_name: str) -> frozenset[str]:
    normalized = stream_name.strip().casefold()
    try:
        return SPECIALIZED_STREAM_EVENT_TYPES[normalized]
    except KeyError as exc:
        raise WebSocketTopicError("Unsupported specialized WebSocket stream.") from exc


def stream_topics(stream_name: str) -> set[str]:
    return {event_type_to_topic(event_type) for event_type in stream_event_types(stream_name)}

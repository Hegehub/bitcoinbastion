import pytest

from app.services.events.websocket_filters import (
    SUPPORTED_TOPICS,
    WebSocketTopicError,
    event_type_to_topic,
    parse_topics,
    should_deliver,
)


def test_empty_topics_returns_all_topics() -> None:
    assert parse_topics(None) == SUPPORTED_TOPICS
    assert parse_topics(" ") == SUPPORTED_TOPICS


def test_topics_parse_trim_case_insensitive_and_deduplicate() -> None:
    assert parse_topics(" Signals, trace ,SIGNALS,market ") == {"signals", "trace", "market"}


def test_invalid_topic_is_rejected() -> None:
    with pytest.raises(WebSocketTopicError):
        parse_topics("signals,unknown")


@pytest.mark.parametrize(
    ("event_type", "topic"),
    [
        ("signal.created", "signals"),
        ("trace.report.created", "trace"),
        ("market.candle.attributed", "market"),
        ("news.article.created", "news"),
        ("onchain.large_transfer", "onchain"),
        ("treasury.approval.required", "treasury"),
        ("provider.degraded", "provider-health"),
        ("intelligence.timeline.updated", "intelligence-timeline"),
        ("something.unregistered", "observability"),
    ],
)
def test_event_type_to_topic(event_type: str, topic: str) -> None:
    assert event_type_to_topic(event_type) == topic


def test_should_deliver_uses_derived_topic() -> None:
    assert should_deliver("trace.report.created", {"trace"})
    assert not should_deliver("trace.report.created", {"signals"})

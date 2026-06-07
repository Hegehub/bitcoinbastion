from app.events.registry import EVENT_REGISTRY
from app.events.types import BastionEventType, EventDomain

EXPECTED_EVENT_TYPES = {
    "news.article.created",
    "news.article.scored",
    "news.event.created",
    "news.event.high_impact",
    "signal.created",
    "signal.published",
    "signal.suppressed",
    "signal.operator_review_required",
    "onchain.large_transfer",
    "onchain.watchlist_hit",
    "onchain.fee_spike",
    "onchain.mempool_pressure",
    "trace.report.created",
    "trace.risk_band.changed",
    "trace.batch.completed",
    "trace.source_disagreement.detected",
    "trace.treasury_destination_check.created",
    "wallet.health.generated",
    "wallet.privacy_risk.high",
    "treasury.request.created",
    "treasury.policy.failed",
    "treasury.approval.required",
    "treasury.request.approved",
    "treasury.request.rejected",
    "policy.execution.failed",
    "policy.warning.created",
    "policy.evaluation.completed",
    "market.regime.changed",
    "market.candle.attributed",
    "market.price_tick.observed",
    "market.candle.closed",
    "evidence.packet.created",
    "evidence.replay.completed",
    "evidence.replay.failed",
    "provider.degraded",
    "provider.recovered",
    "pipeline.lag.high",
    "job.failed",
    "system.degraded_mode.entered",
    "system.degraded_mode.exited",
    "system.runtime_warning.created",
}


def test_all_expected_event_types_exist() -> None:
    assert {event_type.value for event_type in BastionEventType} == EXPECTED_EVENT_TYPES


def test_event_names_are_lowercase_dot_separated_contracts() -> None:
    for event_type in BastionEventType:
        value = event_type.value
        assert value == value.lower()
        assert " " not in value
        assert "." in value
        assert all(part for part in value.split("."))


def test_event_type_values_are_unique() -> None:
    values = [event_type.value for event_type in BastionEventType]
    assert len(values) == len(set(values))


def test_every_event_type_has_registry_metadata() -> None:
    assert set(EVENT_REGISTRY) == set(BastionEventType)


def test_every_event_has_valid_registry_domain() -> None:
    for metadata in EVENT_REGISTRY.values():
        assert metadata.domain in set(EventDomain)

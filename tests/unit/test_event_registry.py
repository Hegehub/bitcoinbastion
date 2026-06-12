from app.events.registry import EVENT_REGISTRY
from app.events.safety import SafetyFlag
from app.events.types import BastionEventType, EventDomain


def test_registry_contains_all_event_types() -> None:
    assert set(EVENT_REGISTRY) == set(BastionEventType)


def test_delivery_and_public_safety_permissions_are_explicit() -> None:
    for metadata in EVENT_REGISTRY.values():
        assert isinstance(metadata.webhook_allowed, bool)
        assert isinstance(metadata.websocket_allowed, bool)
        assert isinstance(metadata.public_safe, bool)
        assert isinstance(metadata.audit_required, bool)


def test_trace_events_are_advisory_and_not_legal_verdicts() -> None:
    trace_events = [meta for meta in EVENT_REGISTRY.values() if meta.domain == EventDomain.TRACE]
    assert trace_events
    for metadata in trace_events:
        assert metadata.contains_legal_verdict is False
        assert SafetyFlag.ADVISORY_ONLY in metadata.safety_flags
        assert SafetyFlag.NOT_LEGAL_VERIFICATION in metadata.safety_flags
        assert SafetyFlag.NOT_BITCOIN_CONSENSUS_PROOF in metadata.safety_flags
        assert SafetyFlag.NO_CUSTODY in metadata.safety_flags


def test_market_and_signal_events_are_not_financial_advice() -> None:
    governed = [
        meta
        for meta in EVENT_REGISTRY.values()
        if meta.domain in {EventDomain.MARKET, EventDomain.SIGNAL}
    ]
    assert governed
    for metadata in governed:
        assert metadata.contains_financial_advice is False
        assert SafetyFlag.NOT_FINANCIAL_ADVICE in metadata.safety_flags


def test_treasury_approval_events_require_operator_review() -> None:
    approval_events = {
        BastionEventType.TREASURY_APPROVAL_REQUIRED,
        BastionEventType.TREASURY_REQUEST_APPROVED,
        BastionEventType.TREASURY_REQUEST_REJECTED,
        BastionEventType.TREASURY_POLICY_FAILED,
    }
    for event_type in approval_events:
        metadata = EVENT_REGISTRY[event_type]
        assert metadata.requires_operator_review is True
        assert SafetyFlag.OPERATOR_REVIEW_REQUIRED in metadata.safety_flags
        assert SafetyFlag.NO_AUTO_EXECUTION in metadata.safety_flags


def test_provider_degradation_events_expose_degraded_state_flags() -> None:
    metadata = EVENT_REGISTRY[BastionEventType.PROVIDER_DEGRADED]
    assert metadata.public_safe is True
    assert metadata.webhook_allowed is True
    assert metadata.websocket_allowed is True
    assert SafetyFlag.DEGRADED_DATA_VISIBLE in metadata.safety_flags
    assert SafetyFlag.STALE_DATA_VISIBLE in metadata.safety_flags

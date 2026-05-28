from datetime import UTC, datetime
from app.services.intelligence.timeline_normalizer import TimelineNormalizationService


def test_normalize_operator_action_utc() -> None:
    svc = TimelineNormalizationService()
    item = svc.normalize_operator_action("signal_approved", datetime.now(UTC))
    assert item["event_type"] == "OPERATOR_ACTION"

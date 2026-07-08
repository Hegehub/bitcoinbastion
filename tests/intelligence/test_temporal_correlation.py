from datetime import UTC, datetime, timedelta
from app.services.intelligence.temporal_correlation import rank_temporal_proximity


def test_rank_temporal_proximity() -> None:
    now = datetime.now(UTC)
    events = [
        {"event_time": now + timedelta(seconds=10)},
        {"event_time": now + timedelta(seconds=2)},
    ]
    ranked = rank_temporal_proximity(events, now)
    assert ranked[0]["event_time"] == events[1]["event_time"]

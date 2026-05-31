from app.services.intelligence.timeline_deduplication import dedup_key


def test_dedup_key_stable() -> None:
    a = dedup_key("X", "2026-01-01T00:00:00+00:00", "t", {"id": 1})
    b = dedup_key("X", "2026-01-01T00:00:00+00:00", "t", {"id": 1})
    assert a == b

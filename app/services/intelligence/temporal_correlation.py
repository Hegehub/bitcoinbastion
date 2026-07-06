from datetime import datetime
from typing import Any, cast


def _et(e: dict[str, Any]) -> datetime:
    return cast(datetime, e["event_time"])


def find_events_before(events: list[dict[str, Any]], at: datetime) -> list[dict[str, Any]]:
    return [e for e in events if _et(e) < at]


def find_events_after(events: list[dict[str, Any]], at: datetime) -> list[dict[str, Any]]:
    return [e for e in events if _et(e) > at]


def find_events_near(
    events: list[dict[str, Any]], at: datetime, seconds: int = 300
) -> list[dict[str, Any]]:
    return [e for e in events if abs((_et(e) - at).total_seconds()) <= seconds]


def find_events_within_window(
    events: list[dict[str, Any]], start: datetime, end: datetime
) -> list[dict[str, Any]]:
    return [e for e in events if start <= _et(e) <= end]


def compute_temporal_distance(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds())


def rank_temporal_proximity(events: list[dict[str, Any]], at: datetime) -> list[dict[str, Any]]:
    return sorted(events, key=lambda e: abs((_et(e) - at).total_seconds()))

"""Base abstractions for future TimescaleDB repositories."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


class TimeSeriesSession(Protocol):
    """Minimal session protocol used by future time-series repositories."""

    def execute(self, statement: Any, parameters: dict[str, Any] | None = None) -> Any: ...


@dataclass(frozen=True)
class TimeRange:
    """Inclusive/exclusive time range for future time-series queries."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("time-series range end must be after start")


class TimeSeriesRepository:
    """Small base class for future TimescaleDB repositories.

    Concrete repositories for BTC price points, candles, mempool fee snapshots,
    provider/source health snapshots, metric usage, and access integrity history
    should implement the domain-specific SQL while preserving PostgreSQL as
    transactional truth for access, entitlement, revocation, recovery, and policy
    decisions.
    """

    table_name: str
    time_column: str = "recorded_at"

    def __init__(self, session: TimeSeriesSession) -> None:
        self.session = session

    async def insert_point(self, point: dict[str, Any]) -> None:
        raise NotImplementedError(
            "Timescale insert_point must be implemented by a concrete repository"
        )

    async def query_range(
        self, time_range: TimeRange, *, limit: int | None = None
    ) -> Sequence[Any]:
        raise NotImplementedError(
            "Timescale query_range must be implemented by a concrete repository"
        )

    async def latest(self, *, limit: int = 1) -> Sequence[Any]:
        raise NotImplementedError("Timescale latest must be implemented by a concrete repository")

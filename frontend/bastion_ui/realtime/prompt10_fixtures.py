"""Deterministic Feature-60 fixtures for typed Prompt-10 tests only."""

from datetime import UTC, datetime

from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.transport.generated_schemas import (
    MarketSourceRef,
    MarketSourceType,
    MarketTimelineEventOut,
    TimelineKind,
)

FIXTURE_PROVENANCE = ProvenanceState.DEMO_FIXTURE

TIMELINE_EVENT_FIXTURE = MarketTimelineEventOut(
    event_id=6001,
    sequence=6001,
    kind=TimelineKind(root="NEWS"),
    producer_type="news_event",
    occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    observed_at=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
    source=MarketSourceRef(
        source_id="fixture:source:1",
        display_name="DEMO_FIXTURE source",
        source_type=MarketSourceType(root="NEWS"),
    ),
    title="DEMO_FIXTURE historical event",
    summary="Schema-correct deterministic fixture; never a production fallback.",
    related_signal_id=None,
    related_candle_id=None,
    evidence_links=[],
    limitations=["DEMO_FIXTURE"],
)

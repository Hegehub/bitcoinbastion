from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.market_narrative import MarketNarrative
from app.db.models.news_source import NewsSource
from app.schemas.market_history import AttributionRelation, TimelineKind
from app.services.intelligence.market_history_service import MarketHistoryService


def _db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_timeline_order_and_replay_are_backend_deterministic() -> None:
    db = _db()
    now = datetime(2026, 8, 12, 12, tzinfo=UTC).replace(tzinfo=None)
    db.add_all(
        [
            IntelligenceTimelineEvent(
                id=1,
                event_type="news_event",
                source_kind="NEWS",
                title="A",
                summary="Observed report",
                event_time=now,
                ingested_at=now,
                updated_at=now,
            ),
            IntelligenceTimelineEvent(
                id=2,
                event_type="signal.published",
                source_kind="SIGNAL",
                title="B",
                summary="Published signal",
                event_time=now,
                ingested_at=now,
                updated_at=now,
            ),
        ]
    )
    db.commit()
    service = MarketHistoryService(db)
    page = service.timeline(limit=10)
    assert [item.event_id for item in page.items] == [2, 1]
    assert page.items[0].kind is TimelineKind.SIGNAL
    first = service.capture_for_event(2)
    second = service.capture_for_event(2)
    assert first == second
    assert first is not None
    assert first.integrity.meaning == "CONTENT_EQUALITY_ONLY"
    assert first.schema_version == "market-replay.capture.v1"


def test_attribution_taxonomy_is_conservative_and_typed() -> None:
    db = _db()
    now = datetime(2026, 8, 12, 12)
    db.add(
        CandleAttribution(
            candle_id=1,
            event_id=None,
            timeframe="1h",
            candle_open_time=now,
            candle_close_time=now,
            attribution_type="correlation_candidate",
            confidence_score=0.75,
            summary_text="Temporal and analytical candidate.",
            limitations_json={"scope": "Association does not prove causality."},
        )
    )
    db.commit()
    item = MarketHistoryService(db).attributions(10)[0]
    assert item.relation is AttributionRelation.CORRELATION_CANDIDATE
    assert item.confidence_ratio == 0.75
    assert "causality" in item.limitations[0]


def test_narrative_and_source_projection_default_deny_internal_fields() -> None:
    db = _db()
    now = datetime(2026, 8, 12, 12)
    db.add(
        MarketNarrative(
            slug="stored",
            name="Stored",
            description="Backend stored narrative.",
            avg_confidence=0.4,
            updated_at=now,
        )
    )
    db.add(
        NewsSource(
            uuid="source-1",
            name="Safe Source",
            kind="rss",
            category="market_media",
            homepage_url="https://example.com/report",
            base_url="https://user:secret@example.com",
            rss_url="https://example.com/private-feed",
            metadata_json={"api_key": "never"},
            is_public=True,
        )
    )
    db.commit()
    service = MarketHistoryService(db)
    narrative = service.narratives(10)[0]
    source = service.sources(10)[0]
    assert narrative.body_plain_text == "Backend stored narrative."
    payload = source.model_dump(mode="json")
    assert payload["homepage_url"] == "https://example.com/report"
    assert "api_key" not in payload and "rss_url" not in payload and "base_url" not in payload


def test_credential_url_is_excluded_not_redacted_into_clickable_link() -> None:
    db = _db()
    db.add(
        NewsSource(
            uuid="source-2",
            name="Unsafe URL",
            kind="rss",
            category="market_media",
            homepage_url="https://user:secret@example.com/report",
            is_public=True,
        )
    )
    db.commit()
    source = MarketHistoryService(db).sources(10)[0]
    assert source.homepage_url is None
    assert source.limitations == ("Configured source URL is not browser-safe.",)

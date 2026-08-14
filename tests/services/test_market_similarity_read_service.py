from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.news_event import NewsEvent
from app.schemas.market_similarity import MarketSimilarityReportOut
from app.services.intelligence.market_similarity_read_service import MarketSimilarityReadService


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _event(event_id: int, title: str, minute: int) -> NewsEvent:
    observed = datetime(2026, 1, 1, 0, minute, tzinfo=timezone.utc)
    return NewsEvent(
        id=event_id,
        canonical_title=title,
        event_type="MARKET",
        event_category="MARKET",
        first_seen_at=observed,
        last_seen_at=observed,
    )


def test_report_preserves_backend_rank_score_and_uncertainty_semantics(db: Session) -> None:
    db.add_all([_event(1, "Reference", 0), _event(2, "Second", 2), _event(3, "First", 3)])
    db.flush()
    db.add_all(
        [
            HistoricalEventSimilarity(
                id=11,
                event_id=1,
                similar_event_id=2,
                similarity_score=0.6,
                pattern_match=False,
                sentiment_match=0.5,
                impact_match=0.7,
                volatility_match=0.4,
            ),
            HistoricalEventSimilarity(
                id=12,
                event_id=1,
                similar_event_id=3,
                similarity_score=0.9,
                pattern_match=True,
                sentiment_match=0.8,
                impact_match=0.9,
                volatility_match=0.7,
            ),
        ]
    )
    db.flush()

    report = MarketSimilarityReadService(db).report(1)

    assert [item.candidate_event_id for item in report.results] == [3, 2]
    assert [item.rank for item in report.results] == [1, 2]
    assert report.results[0].score_ratio == 0.9
    assert report.results[0].score_meaning == "HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE"
    assert report.uncertainty.sample_count == 2
    assert report.uncertainty.confidence_ratio is None
    assert report.uncertainty.sufficiency == "AVAILABLE"
    assert all("predict" in item.limitations[0] for item in report.results)


def test_empty_is_insufficient_not_zero_confidence(db: Session) -> None:
    report = MarketSimilarityReadService(db).report(404)
    assert report.results == ()
    assert report.uncertainty.sufficiency == "INSUFFICIENT"
    assert report.uncertainty.confidence_ratio is None


def test_contract_rejects_noncanonical_rank() -> None:
    payload = MarketSimilarityReadService.__new__(MarketSimilarityReadService)
    del payload
    with pytest.raises(ValueError, match="contiguous backend ranks"):
        MarketSimilarityReportOut.model_validate(
            {
                "reference_event_id": 1,
                "results": [
                    {
                        "result_id": 1,
                        "rank": 2,
                        "reference_event_id": 1,
                        "candidate_event_id": 2,
                        "candidate_title": "Candidate",
                        "candidate_occurred_at": "2026-01-01T00:00:00Z",
                        "replay_event_id": 2,
                        "score_ratio": 0.5,
                        "dimensions": [],
                        "limitations": [],
                    }
                ],
                "uncertainty": {
                    "sufficiency": "AVAILABLE",
                    "sample_count": 1,
                    "coverage_dimension_count": 4,
                },
                "generated_at": "2026-01-01T00:00:00Z",
            }
        )

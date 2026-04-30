from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news import NewsArticle, NewsSource
from app.db.models.onchain import OnchainEvent
from app.db.models.signal import Signal
from app.db.models.signal_link import SignalSourceLink
from app.tasks.signal_tasks import generate_signals_for_sources


def test_generate_signals_for_sources_persists_and_links_news_and_onchain() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        source = NewsSource(name="Example", rss_url="https://example.com/rss")
        db.add(source)
        db.commit()
        db.refresh(source)

        db.add(
            NewsArticle(
                source_id=source.id,
                title="BTC market update",
                url="https://example.com/btc-market-update",
                content_hash="hash-news-1",
                published_at=datetime.now(UTC),
                summary="Relevant BTC market update",
                btc_relevance_score=0.9,
                urgency_score=0.7,
                impact_score=0.8,
                confidence_score=0.85,
            )
        )
        db.add(
            OnchainEvent(
                event_type="large_transfer",
                txid="abc123",
                address="bc1qexample",
                value_sats=125_000_000,
                significance_score=0.82,
                confidence_score=0.9,
                observed_at=datetime.now(UTC),
            )
        )
        db.commit()

        generated = generate_signals_for_sources(db, limit_per_source=10)
        assert generated >= 2

        signals = list(db.execute(select(Signal).order_by(Signal.id.asc())).scalars())
        assert len(signals) >= 2
        assert all(item.source_refs_json not in ("[]", "") for item in signals)

        links = list(db.execute(select(SignalSourceLink)).scalars())
        assert len(links) >= 2
        assert {item.source_type for item in links} >= {"news_article", "onchain_event"}

        generated_second_run = generate_signals_for_sources(db, limit_per_source=10)
        assert generated_second_run == 0


def test_generate_signals_for_sources_deduplicates_onchain_identity() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        now = datetime.now(UTC)
        db.add(
            OnchainEvent(
                event_type="large_transfer",
                txid="dup-tx-1",
                address="bc1qdup",
                value_sats=50_000_000,
                significance_score=0.91,
                confidence_score=0.9,
                block_height=900_000,
                observed_at=now,
            )
        )
        db.add(
            OnchainEvent(
                event_type="large_transfer",
                txid="dup-tx-1",
                address="bc1qdup",
                value_sats=50_000_000,
                significance_score=0.91,
                confidence_score=0.9,
                block_height=900_000,
                observed_at=now,
            )
        )
        db.commit()

        generated = generate_signals_for_sources(db, limit_per_source=10)
        assert generated == 1

        links = list(db.execute(select(SignalSourceLink)).scalars())
        onchain_links = [item for item in links if item.source_type == "onchain_event"]
        assert len(onchain_links) == 1
        assert onchain_links[0].source_id.startswith("dup-tx-1:large_transfer:900000")

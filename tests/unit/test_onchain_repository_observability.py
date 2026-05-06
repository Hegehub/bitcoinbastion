from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import ChainEvent


def test_onchain_repository_tracks_provider_counts_last_24h() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        repo = OnchainRepository(db)
        repo.add_event(
            ChainEvent(
                event_type="mempool_recent_tx",
                txid="prov-1",
                address="bc1qprov",
                value_sats=1000,
                block_height=900_000,
                observed_at=datetime.now(UTC),
                payload={"provider": "esplora"},
            ),
            significance=0.5,
        )
        counts = repo.provider_counts_last_24h()
    assert counts and counts[0][0] == "esplora"

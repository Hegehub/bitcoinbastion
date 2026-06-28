import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.projections.clickhouse_projector import ClickHouseOutboxProjector
from tests.unit.test_clickhouse_projector_mapping import make_event


class FakeAnalyticsStore:
    async def insert_events(self, table: str, events: list[dict[str, object]]):  # pragma: no cover
        raise AssertionError("disabled projector must not insert")


def test_clickhouse_disabled_projector_returns_disabled_summary() -> None:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(make_event("api.usage.event"))
        db.commit()
        projector = ClickHouseOutboxProjector(
            settings=Settings(_env_file=None, CLICKHOUSE_ENABLED=False),
            outbox_repository=StorageOutboxRepository(db),
            analytics_store=FakeAnalyticsStore(),
        )
        summary = asyncio.run(projector.project_batch())

    assert summary.clickhouse_enabled is False
    assert summary.processed == 0
    assert summary.reason == "clickhouse_disabled"

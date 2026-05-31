from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.base import Base
from app.services.intelligence.timeline_service import TimelineService


def test_context_empty() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        ctx = TimelineService().get_event_context(db, 1)
        assert ctx["event"] is None

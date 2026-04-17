from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.signal_repository import SignalRepository


def _signal(title: str, dominant: str) -> Signal:
    return Signal(
        signal_type="news",
        severity="medium",
        score=0.5,
        confidence=0.6,
        title=title,
        summary="summary",
        created_at=datetime.now(UTC),
        explainability_json=f'{{"horizons": {{"dominant": "{dominant}"}}}}',
    )


def test_signal_repository_can_filter_top_by_horizon() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repo = SignalRepository(db)
        repo.add(_signal("short one", "short"))
        repo.add(_signal("long one", "long"))

        long_only = repo.top(limit=10, offset=0, horizon="long")

    assert len(long_only) == 1
    assert long_only[0].title == "long one"

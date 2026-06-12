import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox, EventOutboxStatus


def test_event_outbox_model_can_be_created_with_defaults() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])

    with Session(engine) as db:
        item = EventOutbox(
            event_id="00000000-0000-0000-0000-000000000001",
            event_type="trace.report.created",
            domain="trace",
            payload_json=json.dumps({"report_id": 1}),
            metadata_json=json.dumps({"source": "test"}),
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        assert item.id is not None
        assert item.status == EventOutboxStatus.PENDING.value
        assert item.attempts == 0
        assert item.max_attempts == 5
        assert item.event_version == 1
        assert json.loads(item.payload_json) == {"report_id": 1}
        assert json.loads(item.metadata_json) == {"source": "test"}


def test_event_id_is_unique() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])

    with Session(engine) as db:
        first = EventOutbox(
            event_id="00000000-0000-0000-0000-000000000002",
            event_type="signal.created",
            domain="signal",
            payload_json="{}",
            metadata_json="{}",
        )
        duplicate = EventOutbox(
            event_id="00000000-0000-0000-0000-000000000002",
            event_type="signal.created",
            domain="signal",
            payload_json="{}",
            metadata_json="{}",
        )
        db.add(first)
        db.commit()
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()

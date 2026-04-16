from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.entity import Entity
from app.services.reputation.entity_provenance_service import EntityProvenanceService


def test_entity_provenance_refresh_updates_confidence_on_drift() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        db.add(
            Entity(
                name="Exchange A",
                entity_type="exchange",
                confidence=0.2,
                source_refs_json='["a","b","c","d","e","f"]',
            )
        )
        db.commit()

        out = EntityProvenanceService().refresh(db=db, limit=20)
        refreshed = db.query(Entity).first()

    assert out.scanned == 1
    assert out.updated == 1
    assert out.drifted == 1
    assert refreshed is not None
    assert refreshed.confidence > 0.2
    assert out.deltas
    assert out.deltas[0].entity_id == refreshed.id


def test_entity_provenance_refresh_no_update_when_no_entities() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        out = EntityProvenanceService().refresh(db=db)

    assert out.scanned == 0
    assert out.updated == 0
    assert out.drifted == 0
    assert out.deltas == []

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.entity import Entity
from app.db.models.watched_entity import WatchedEntity


class EntityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_entities(
        self,
        *,
        limit: int,
        offset: int,
        query: str | None = None,
        entity_type: str | None = None,
        min_confidence: float | None = None,
    ) -> list[Entity]:
        stmt = select(Entity).order_by(Entity.updated_at.desc()).limit(limit).offset(offset)
        if query:
            stmt = stmt.where(Entity.name.ilike(f"%{query}%"))
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        if min_confidence is not None:
            stmt = stmt.where(Entity.confidence >= min_confidence)

        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

    def count_entities(
        self,
        *,
        query: str | None = None,
        entity_type: str | None = None,
        min_confidence: float | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Entity)
        if query:
            stmt = stmt.where(Entity.name.ilike(f"%{query}%"))
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        if min_confidence is not None:
            stmt = stmt.where(Entity.confidence >= min_confidence)

        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

    def list_watchlist(self, *, user_id: int, limit: int, offset: int) -> list[WatchedEntity]:
        stmt = (
            select(WatchedEntity)
            .where(WatchedEntity.user_id == user_id)
            .where(WatchedEntity.is_active.is_(True))
            .order_by(WatchedEntity.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

    def count_watchlist(self, *, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(WatchedEntity)
            .where(WatchedEntity.user_id == user_id)
            .where(WatchedEntity.is_active.is_(True))
        )
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

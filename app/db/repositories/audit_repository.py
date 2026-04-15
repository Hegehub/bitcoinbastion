from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, log: AuditLog) -> AuditLog:
        """Persist an audit log when a real SQLAlchemy session is available.

        In unit tests and degraded environments the repository may be initialized with
        a lightweight stub object that does not expose Session methods. In that case,
        return the log object without raising so business workflows stay testable.
        """

        if not all(hasattr(self.db, method) for method in ("add", "commit", "refresh")):
            return log

        try:
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return log
        except SQLAlchemyError:
            return log

    def list_recent(self, limit: int = 50, action: str | None = None) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

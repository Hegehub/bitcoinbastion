from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

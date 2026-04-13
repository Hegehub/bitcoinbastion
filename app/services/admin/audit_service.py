import json

from app.db.models.audit import AuditLog
from app.db.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        self.repo = repo

    def record_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_user_id: int | None = None,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=json.dumps(before or {}),
            after_json=json.dumps(after or {}),
        )
        return self.repo.record(log)

from sqlalchemy.orm import Session
from typing import Literal

from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.admin import RecoveryCheckOut, RecoveryIssueOut


class RecoveryCheckService:
    def evaluate(self, db: Session) -> RecoveryCheckOut:
        job_repo = JobRunRepository(db)
        delivery_repo = DeliveryRepository(db)

        failed_jobs = job_repo.failed_count_last_24h()
        failed_deliveries = delivery_repo.failed_count_last_24h()

        issues: list[RecoveryIssueOut] = []
        for run in job_repo.list_recent_failures(limit=10):
            issues.append(
                RecoveryIssueOut(
                    issue_type="job_failure",
                    reference=run.task_name,
                    occurred_at=run.started_at,
                    detail=run.error_message or "Job run failed without explicit error payload.",
                )
            )

        for item in delivery_repo.list_recent_failures(limit=10):
            issues.append(
                RecoveryIssueOut(
                    issue_type="delivery_failure",
                    reference=f"signal:{item.signal_id}",
                    occurred_at=item.sent_at,
                    detail=f"Destination={item.destination}, status={item.delivery_status}",
                )
            )

        recommended_actions: list[str] = []
        if failed_jobs > 0:
            recommended_actions.append("Inspect failed jobs and retry safe task types via /api/v1/admin/jobs/retry.")
        if failed_deliveries > 0:
            recommended_actions.append("Review failed deliveries and rerun delivery.publish after destination checks.")
        if not recommended_actions:
            recommended_actions.append("No recovery action required. Continue routine observability checks.")

        severity = self._severity(failed_jobs=failed_jobs, failed_deliveries=failed_deliveries)

        return RecoveryCheckOut(
            ok=(severity == "ok"),
            severity=severity,
            failed_jobs_24h=failed_jobs,
            failed_deliveries_24h=failed_deliveries,
            issues=issues[:20],
            recommended_actions=recommended_actions,
        )

    @staticmethod
    def _severity(
        *, failed_jobs: int, failed_deliveries: int
    ) -> Literal["ok", "warning", "critical"]:
        if failed_jobs >= 10 or failed_deliveries >= 6:
            return "critical"
        if failed_jobs > 0 or failed_deliveries > 0:
            return "warning"
        return "ok"

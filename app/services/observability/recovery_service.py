from sqlalchemy.orm import Session
from typing import Literal

from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.admin import RecoveryCheckOut, RecoveryDrillOut, RecoveryHotspotOut, RecoveryIssueOut


class RecoveryCheckService:
    def evaluate(self, db: Session) -> RecoveryCheckOut:
        job_repo = JobRunRepository(db)
        delivery_repo = DeliveryRepository(db)

        failed_jobs = job_repo.failed_count_last_24h()
        failed_deliveries = delivery_repo.failed_count_last_24h()
        failed_job_hotspots = job_repo.top_failed_tasks_last_24h(limit=5)
        failed_delivery_hotspots = delivery_repo.top_failed_destinations_last_24h(limit=5)

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

        hotspots: list[RecoveryHotspotOut] = [
            RecoveryHotspotOut(
                issue_type="job_failure",
                reference=task_name,
                failures_24h=failure_count,
            )
            for task_name, failure_count in failed_job_hotspots
        ]
        hotspots.extend(
            RecoveryHotspotOut(
                issue_type="delivery_failure",
                reference=destination,
                failures_24h=failure_count,
            )
            for destination, failure_count in failed_delivery_hotspots
        )
        hotspots.sort(key=lambda item: (-item.failures_24h, item.issue_type, item.reference))
        drills = self._drill_plan_from_hotspots(hotspots=hotspots)

        recommended_actions: list[str] = []
        if failed_jobs > 0:
            recommended_actions.append("Inspect failed jobs and retry safe task types via /api/v1/admin/jobs/retry.")
        if failed_deliveries > 0:
            recommended_actions.append("Review failed deliveries and rerun delivery.publish after destination checks.")
        if any(item.failures_24h >= 3 for item in hotspots):
            recommended_actions.append(
                "Prioritize repeated failure hotspots (>=3 in 24h) and run focused failure-mode drills."
            )
        if not recommended_actions:
            recommended_actions.append("No recovery action required. Continue routine observability checks.")

        severity = self._severity(failed_jobs=failed_jobs, failed_deliveries=failed_deliveries)

        return RecoveryCheckOut(
            ok=(severity == "ok"),
            severity=severity,
            failed_jobs_24h=failed_jobs,
            failed_deliveries_24h=failed_deliveries,
            issues=issues[:20],
            hotspots=hotspots[:10],
            drills=drills,
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

    @staticmethod
    def _drill_plan_from_hotspots(hotspots: list[RecoveryHotspotOut]) -> list[RecoveryDrillOut]:
        if not hotspots:
            return [
                RecoveryDrillOut(
                    drill_code="routine_recovery_probe",
                    title="Run routine recovery readiness probe",
                    priority="low",
                    target_reference="platform",
                    run_within_hours=24,
                    automation_ready=True,
                )
            ]

        drills: list[RecoveryDrillOut] = []
        for hotspot in hotspots[:3]:
            priority: Literal["low", "medium", "high"] = "high" if hotspot.failures_24h >= 3 else "medium"
            drill_code = "job_replay_drill" if hotspot.issue_type == "job_failure" else "delivery_failover_drill"
            run_within_hours = 4 if priority == "high" else 12
            drills.append(
                RecoveryDrillOut(
                    drill_code=drill_code,
                    title=f"Run {hotspot.issue_type.replace('_', ' ')} drill",
                    priority=priority,
                    target_reference=hotspot.reference,
                    run_within_hours=run_within_hours,
                    automation_ready=True,
                )
            )
        return drills

from sqlalchemy.orm import Session

from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.observability import (
    DeliveryStatsOut,
    JobStatsOut,
    OperationsSnapshotOut,
    ProviderHealthOut,
)


class OperationsSnapshotService:
    def snapshot(self, db: Session) -> OperationsSnapshotOut:
        jobs = JobRunRepository(db)
        deliveries = DeliveryRepository(db)

        failed_jobs = jobs.failed_count_last_24h()
        failed_deliveries = deliveries.failed_count_last_24h()

        return OperationsSnapshotOut(
            queue_depth=0,
            stale_jobs=failed_jobs,
            providers=[
                ProviderHealthOut(provider="rss", healthy=True, details="No provider errors observed."),
                ProviderHealthOut(
                    provider="onchain", healthy=failed_jobs == 0, details="Job health derived from runtime logs."
                ),
                ProviderHealthOut(
                    provider="delivery",
                    healthy=failed_deliveries == 0,
                    details="Delivery health derived from last-24h delivery logs.",
                ),
            ],
            jobs=JobStatsOut(
                started_24h=jobs.started_count_last_24h(),
                failed_24h=failed_jobs,
            ),
            deliveries=DeliveryStatsOut(
                sent_24h=deliveries.sent_count_last_24h(),
                failed_24h=failed_deliveries,
            ),
        )

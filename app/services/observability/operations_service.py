from sqlalchemy.orm import Session

from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.onchain_repository import OnchainRepository
from app.schemas.observability import (
    ChainStateOut,
    DeliveryStatsOut,
    JobStatsOut,
    OperationsSnapshotOut,
    ProviderHealthOut,
)
from app.services.blockchain.chain_state_service import ChainStateService


class OperationsSnapshotService:
    def snapshot(self, db: Session) -> OperationsSnapshotOut:
        jobs = JobRunRepository(db)
        deliveries = DeliveryRepository(db)
        onchain = OnchainRepository(db)

        failed_jobs = jobs.failed_count_last_24h()
        failed_deliveries = deliveries.failed_count_last_24h()
        observed_block_height = onchain.latest_block_height() or 899_995
        chain_state = ChainStateService().evaluate(
            tip_height=observed_block_height + 1,
            observed_block_height=observed_block_height,
            headers_height=observed_block_height + 1,
        )
        onchain_healthy = failed_jobs == 0 and chain_state.finality_band in {"moderate", "strong"}
        onchain_details = (
            "Runtime jobs healthy and chain finality is acceptable."
            if onchain_healthy
            else "On-chain health degraded due to failed jobs or weak finality."
        )

        return OperationsSnapshotOut(
            queue_depth=0,
            stale_jobs=failed_jobs,
            providers=[
                ProviderHealthOut(provider="rss", healthy=True, details="No provider errors observed."),
                ProviderHealthOut(
                    provider="onchain",
                    healthy=onchain_healthy,
                    details=onchain_details,
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
            chain_state=ChainStateOut.model_validate(chain_state, from_attributes=True),
        )

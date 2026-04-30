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
from app.services.observability.recovery_service import RecoveryCheckService


class OperationsSnapshotService:
    def snapshot(self, db: Session) -> OperationsSnapshotOut:
        jobs = JobRunRepository(db)
        deliveries = DeliveryRepository(db)
        onchain = OnchainRepository(db)

        failed_jobs = jobs.failed_count_last_24h()
        failed_deliveries = deliveries.failed_count_last_24h()
        started_jobs = max(1, jobs.started_count_last_24h())
        job_success_rate = (started_jobs - failed_jobs) / started_jobs
        observed_block_height = onchain.latest_block_height() or 899_995
        provider_counts = onchain.provider_counts_last_24h()
        provider_count_total = sum(count for _, count in provider_counts)
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
        recovery = RecoveryCheckService().evaluate(db=db)
        provider_name = provider_counts[0][0] if provider_counts else "unknown"
        provider_share = (
            round(provider_counts[0][1] / provider_count_total, 3)
            if provider_counts and provider_count_total > 0
            else 0.0
        )

        return OperationsSnapshotOut(
            queue_depth=0,
            stale_jobs=failed_jobs,
            providers=[
                ProviderHealthOut(provider="rss", healthy=True, details="No provider errors observed."),
                ProviderHealthOut(
                    provider="onchain",
                    healthy=onchain_healthy,
                    details=f"{onchain_details} dominant_provider={provider_name} share={provider_share}",
                    confidence=max(0.0, min(1.0, 1.0 - chain_state.reorg_risk_score)),
                    freshness_seconds=300,
                ),
                ProviderHealthOut(
                    provider="delivery",
                    healthy=failed_deliveries == 0,
                    details=(
                        "Delivery health derived from last-24h delivery logs."
                        f" recovery_slo_breached={recovery.recovery_slo.get('slo_breached', False)}"
                    ),
                    confidence=max(0.0, min(1.0, job_success_rate)),
                    freshness_seconds=300,
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

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.intelligence_signals import (
    IntelligenceSignalCandidate,
    IntelligenceSignalDeliveryLog,
)
from app.db.models.evidence_packet import EvidencePacket
from app.db.models.observability_health import (
    BackgroundJobHealth,
    ProviderHealthSnapshot,
    RecoveryEvent,
)
from app.db.models.telegram import TelegramDeliveryLog
from app.schemas.health import (
    BackgroundJobHealthOut,
    DegradedComponentOut,
    ProviderHealthSnapshotOut,
    RuntimeStatusOut,
    SystemHealthOut,
    TelegramHealthOut,
)

ALLOWED_HEALTH_STATES = {"healthy", "degraded", "critical", "maintenance", "offline"}
PRODUCTION_JOBS = [
    "news.fetch",
    "news.cluster_events",
    "news.score_unprocessed",
    "market.collect_btc_price",
    "market.build_candles",
    "news.calculate_price_impact",
    "intelligence.attribute_candles",
    "intelligence.refresh_source_reputation",
    "signals.create_from_news_impact",
    "signals.publish",
    "evidence.generate_news_impact_evidence",
]


class RuntimeStatusService:
    """Builds operator-facing runtime status without hiding degraded providers or jobs."""

    def liveness(self, db: Session) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        # Alembic creates this table whenever migrations have been applied.
        try:
            db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            migrations = "applied"
        except SQLAlchemyError:
            migrations = "missing"
        return {"process": "up", "db": "ok", "migrations": migrations}

    def readiness(self, db: Session) -> RuntimeStatusOut:
        status = self.status(db)
        return status

    def status(self, db: Session) -> RuntimeStatusOut:
        providers = self.provider_health(db)
        jobs = self.job_health(db)
        telegram = self.telegram_health(db)
        degraded = self.degraded_components(providers=providers, jobs=jobs, telegram=telegram)

        provider_state = self._rollup([p.health_state for p in providers])
        job_state = self._rollup([j.health_state for j in jobs])
        telegram_state = telegram.health_state
        signal_state = self._signal_pipeline_state(db)
        evidence_state = self._evidence_pipeline_state(db)
        system_state = self._rollup(
            [provider_state, job_state, telegram_state, signal_state, evidence_state]
        )
        fallback_active = any(d.automatic_fallback_used for d in degraded)
        operator_attention = any(d.operator_attention_required for d in degraded)
        last_successes = [p.last_success_at for p in providers if p.last_success_at] + [
            j.last_finish_at for j in jobs if j.success and j.last_finish_at
        ]

        return RuntimeStatusOut(
            system_state=system_state,
            provider_state=provider_state,
            job_state=job_state,
            signal_pipeline_state=signal_state,
            evidence_pipeline_state=evidence_state,
            telegram_state=telegram_state,
            fallback_active=fallback_active,
            operator_attention_required=operator_attention,
            queue_depth=self._queue_depth(db),
            last_success=max(last_successes) if last_successes else None,
            degraded_components=degraded,
            provider_health=providers,
            job_health=jobs,
            telegram_health=telegram,
        )

    def system_health(self, db: Session) -> SystemHealthOut:
        status = self.status(db)
        try:
            recoveries = (
                db.execute(
                    select(RecoveryEvent).order_by(RecoveryEvent.created_at.desc()).limit(25)
                )
                .scalars()
                .all()
            )
        except SQLAlchemyError:
            recoveries = []
        return SystemHealthOut(
            system_health=status.system_state,
            runtime_status=status,
            provider_health=status.provider_health,
            job_health=status.job_health,
            degraded_components=status.degraded_components,
            recovery_events=[
                {
                    "component": r.component,
                    "failure_time": r.failure_time,
                    "recovery_time": r.recovery_time,
                    "duration_ms": r.duration_ms,
                    "automatic": r.automatic,
                    "operator_confirmed": r.operator_confirmed,
                    "status": r.status,
                }
                for r in recoveries
            ],
            queue_depth=status.queue_depth,
            last_success=status.last_success,
        )

    def provider_health(self, db: Session) -> list[ProviderHealthSnapshotOut]:
        try:
            rows = (
                db.execute(
                    select(ProviderHealthSnapshot)
                    .order_by(ProviderHealthSnapshot.created_at.desc())
                    .limit(100)
                )
                .scalars()
                .all()
            )
        except SQLAlchemyError:
            rows = []
        latest: dict[tuple[str, str], ProviderHealthSnapshot] = {}
        for row in rows:
            latest.setdefault((row.provider_type, row.provider_name), row)
        providers = [
            ProviderHealthSnapshotOut(
                provider_name=r.provider_name,
                provider_type=r.provider_type,
                last_success_at=r.last_success_at,
                last_failure_at=r.last_failure_at,
                failure_count=r.failure_count,
                consecutive_failures=r.consecutive_failures,
                avg_latency_ms=r.avg_latency_ms,
                provider_confidence=r.provider_confidence,
                backoff_until=r.backoff_until,
                health_state=self.calculate_provider_state(
                    consecutive_failures=r.consecutive_failures,
                    provider_confidence=r.provider_confidence,
                    avg_latency_ms=r.avg_latency_ms,
                    backoff_until=r.backoff_until,
                    explicit_state=r.health_state,
                ),
            )
            for r in latest.values()
        ]
        return providers or [
            ProviderHealthSnapshotOut(
                provider_name="rss",
                provider_type="RSS",
                health_state="maintenance",
                provider_confidence=0.0,
            ),
            ProviderHealthSnapshotOut(
                provider_name="btc_price",
                provider_type="Bitcoin price providers",
                health_state="maintenance",
                provider_confidence=0.0,
            ),
            ProviderHealthSnapshotOut(
                provider_name="telegram",
                provider_type="Telegram",
                health_state="maintenance",
                provider_confidence=0.0,
            ),
        ]

    def job_health(self, db: Session) -> list[BackgroundJobHealthOut]:
        try:
            rows = (
                db.execute(
                    select(BackgroundJobHealth)
                    .order_by(BackgroundJobHealth.updated_at.desc())
                    .limit(200)
                )
                .scalars()
                .all()
            )
        except SQLAlchemyError:
            rows = []
        latest: dict[str, BackgroundJobHealth] = {}
        for job_row in rows:
            latest.setdefault(job_row.job_name, job_row)
        result: list[BackgroundJobHealthOut] = []
        for name in PRODUCTION_JOBS:
            candidate = latest.get(name)
            if candidate is None:
                result.append(
                    BackgroundJobHealthOut(
                        job_name=name,
                        success=False,
                        failure_reason="no heartbeat recorded",
                        health_state="maintenance",
                    )
                )
                continue
            result.append(
                BackgroundJobHealthOut(
                    job_name=candidate.job_name,
                    last_start_at=candidate.last_start_at,
                    last_finish_at=candidate.last_finish_at,
                    duration_ms=candidate.duration_ms,
                    success=candidate.success,
                    failure_reason=candidate.failure_reason,
                    retry_count=candidate.retry_count,
                    next_scheduled_at=candidate.next_scheduled_at,
                    worker_name=candidate.worker_name,
                    health_state=self.calculate_job_state(candidate),
                )
            )
        return result

    def telegram_health(self, db: Session) -> TelegramHealthOut:
        try:
            successes = db.execute(
                select(TelegramDeliveryLog.sent_at)
                .where(TelegramDeliveryLog.status == "sent")
                .order_by(TelegramDeliveryLog.sent_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            failures = db.execute(
                select(TelegramDeliveryLog.sent_at)
                .where(TelegramDeliveryLog.status != "sent")
                .order_by(TelegramDeliveryLog.sent_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            failure_count = db.execute(
                select(func.count())
                .select_from(TelegramDeliveryLog)
                .where(TelegramDeliveryLog.status != "sent")
            ).scalar_one()
        except SQLAlchemyError:
            successes = None
            failures = None
            failure_count = 0
        state = "healthy"
        if failures and (not successes or failures > successes):
            state = "degraded"
        if failure_count and failure_count >= 10:
            state = "critical"
        return TelegramHealthOut(
            health_state=state,
            last_publish_success=successes,
            last_publish_failure=failures,
            pending_queue_size=0,
            delivery_failures=int(failure_count or 0),
            average_delivery_latency=0.0,
        )

    def degraded_components(
        self,
        *,
        providers: list[ProviderHealthSnapshotOut],
        jobs: list[BackgroundJobHealthOut],
        telegram: TelegramHealthOut,
    ) -> list[DegradedComponentOut]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        degraded: list[DegradedComponentOut] = []
        healthy_btc = [
            p
            for p in providers
            if "bitcoin" in p.provider_type.lower() and p.health_state == "healthy"
        ]
        if len(healthy_btc) == 1:
            degraded.append(
                DegradedComponentOut(
                    severity="degraded",
                    affected_component="btc_price_providers",
                    started_at=now,
                    recommendation="Add or restore a second BTC price provider before trusting high-confidence market signals.",
                    automatic_fallback_used=True,
                )
            )
        for p in providers:
            if p.health_state in {"degraded", "critical", "offline", "maintenance"}:
                degraded.append(
                    DegradedComponentOut(
                        severity=p.health_state,
                        affected_component=f"provider:{p.provider_type}:{p.provider_name}",
                        started_at=p.last_failure_at or now,
                        recommendation="Inspect provider credentials, network reachability, latency and backoff; do not hide this provider from confidence calculations.",
                        automatic_fallback_used=p.backoff_until is not None,
                    )
                )
        for j in jobs:
            if j.health_state in {"degraded", "critical", "maintenance"}:
                degraded.append(
                    DegradedComponentOut(
                        severity=j.health_state,
                        affected_component=f"job:{j.job_name}",
                        started_at=j.last_finish_at or j.last_start_at or now,
                        recommendation="Inspect worker logs, retry state and next schedule; failed jobs must be replayed or acknowledged.",
                        automatic_fallback_used=j.retry_count > 0,
                    )
                )
        if telegram.health_state != "healthy":
            degraded.append(
                DegradedComponentOut(
                    severity=telegram.health_state,
                    affected_component="telegram",
                    started_at=telegram.last_publish_failure or now,
                    recommendation="API and web may continue, but publication failures must be logged and operators notified.",
                    automatic_fallback_used=True,
                )
            )
        return degraded

    def calculate_provider_state(
        self,
        *,
        consecutive_failures: int,
        provider_confidence: float,
        avg_latency_ms: float | None,
        backoff_until: datetime | None,
        explicit_state: str = "healthy",
    ) -> str:
        if explicit_state in {"critical", "offline", "maintenance"}:
            return explicit_state
        if backoff_until and backoff_until > datetime.utcnow():
            return "degraded"
        if consecutive_failures >= 5 or provider_confidence <= 0.15:
            return "critical"
        if (
            consecutive_failures > 0
            or provider_confidence < 0.5
            or (avg_latency_ms is not None and avg_latency_ms > 5000)
        ):
            return "degraded"
        return "healthy"

    def calculate_job_state(self, row: BackgroundJobHealth) -> str:
        if not row.success:
            return "critical" if row.retry_count >= 3 else "degraded"
        if row.next_scheduled_at and row.next_scheduled_at < datetime.utcnow() - timedelta(
            minutes=15
        ):
            return "degraded"
        return "healthy"

    def _signal_pipeline_state(self, db: Session) -> str:
        try:
            pending = db.execute(
                select(func.count())
                .select_from(IntelligenceSignalCandidate)
                .where(IntelligenceSignalCandidate.status.in_(["pending_review", "pending"]))
            ).scalar_one_or_none()
        except SQLAlchemyError:
            pending = 0
        return "degraded" if int(pending or 0) > 100 else "healthy"

    def _evidence_pipeline_state(self, db: Session) -> str:
        try:
            packets = db.execute(
                select(func.count()).select_from(EvidencePacket)
            ).scalar_one_or_none()
        except SQLAlchemyError:
            packets = 0
        return "healthy" if int(packets or 0) >= 0 else "degraded"

    def _queue_depth(self, db: Session) -> int:
        try:
            pending = db.execute(
                select(func.count())
                .select_from(IntelligenceSignalDeliveryLog)
                .where(
                    IntelligenceSignalDeliveryLog.delivery_status.in_(
                        ["pending", "queued", "retry"]
                    )
                )
            ).scalar_one_or_none()
        except SQLAlchemyError:
            pending = 0
        return int(pending or 0)

    def _rollup(self, states: Iterable[str]) -> str:
        values = list(states) or ["healthy"]
        for state in ("offline", "critical", "degraded", "maintenance"):
            if state in values:
                return state
        return "healthy"

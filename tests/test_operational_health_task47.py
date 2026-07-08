from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.telemetry import OBSERVABILITY_METRIC_NAMES, bounded_label
from app.db.base import Base
from app.schemas.operations import OperationalProviderStatusOut
from app.services.observability.disaster_recovery_service import (
    DisasterRecoveryService,
    REPLAY_TYPES,
)
from app.services.observability.operational_health_service import OperationalHealthService


def test_operational_health_dto_and_readiness_contract() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        health = OperationalHealthService().health(db)
        assert health.degraded_state_visible is True
        assert health.operator_visible is True
        assert health.readiness_status in {"ready", "degraded"}
        readiness = OperationalHealthService().readiness(db)
        assert {
            "news_provider",
            "price_provider",
            "timeline_engine",
            "database",
            "scheduler",
        }.issubset(readiness.details)


def test_provider_degradation_and_recovery_status_rollup() -> None:
    service = OperationalHealthService()
    providers = [
        OperationalProviderStatusOut(provider_name="rss", provider_type="news", status="offline"),
        OperationalProviderStatusOut(
            provider_name="rss2", provider_type="news", status="recovering"
        ),
    ]
    assert service._engine_status(providers, "news") == "offline"
    providers[0].status = "healthy"
    assert service._engine_status(providers, "news") == "recovering"


def test_backup_validation_records_required_fields() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        out = DisasterRecoveryService().verify_backup(
            db, backup_id="backup-001", objects_checked=5, integrity_verified=True
        )
        assert out.backup_id == "backup-001"
        assert out.success is True
        assert out.objects_checked == 5
        assert out.integrity_verified is True
        assert out.limitations == []


def test_restore_validation_requires_full_replay_set() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        failed = DisasterRecoveryService().verify_restore(
            db,
            recovery_id="restore-001",
            replay_types=["news_event"],
            integrity_verified=True,
            deterministic_rebuild_verified=True,
        )
        assert failed.success is False
        assert failed.limitations
        passed = DisasterRecoveryService().verify_restore(
            db,
            recovery_id="restore-002",
            replay_types=REPLAY_TYPES,
            integrity_verified=True,
            deterministic_rebuild_verified=True,
        )
        assert passed.success is True
        assert passed.deterministic_rebuild_verified is True


def test_task47_metrics_registration_and_bounded_labels() -> None:
    required = {
        "news_articles_processed_total",
        "market_price_points_total",
        "btc_candles_generated_total",
        "historical_similarity_queries_total",
        "cronjob_failures_total",
        "dr_recovery_runs_total",
        "backup_validation_runs_total",
    }
    assert required.issubset(set(OBSERVABILITY_METRIC_NAMES))
    assert bounded_label("provider_type", "https://example.com") == "unknown"
    assert bounded_label("timeframe", "1h") == "1h"

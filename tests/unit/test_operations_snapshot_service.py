from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.delivery import DeliveryLog
from app.db.models.job_run import JobRun
from app.db.models.signal import Signal
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.blockchain.chain_state_service import ChainStateEvaluation
from app.services.observability.operations_service import OperationsSnapshotService


def test_operations_snapshot_includes_job_and_delivery_stats() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        runs = JobRunRepository(db)
        started = runs.start("delivery.publish")
        runs.finish(started, status="failed", error_message="network timeout")

        signal = SignalRepository(db).add(
            Signal(
                signal_type="news",
                severity="high",
                score=0.9,
                confidence=0.9,
                title="Delivery test signal",
                summary="summary",
            )
        )
        DeliveryRepository(db).record_sent(
            signal_id=signal.id,
            destination="dry-run",
            payload_snapshot={"title": signal.title},
        )

        snapshot = OperationsSnapshotService().snapshot(db=db)

    assert snapshot.jobs.started_24h >= 1
    assert snapshot.jobs.failed_24h >= 1
    assert snapshot.deliveries.sent_24h >= 1
    assert any(item.provider == "delivery" for item in snapshot.providers)
    assert snapshot.chain_state.tip_height >= snapshot.chain_state.observed_block_height
    assert snapshot.chain_state.finality_band in {"weak", "moderate", "strong"}
    onchain = next(item for item in snapshot.providers if item.provider == "onchain")
    assert onchain.healthy is False
    assert "degraded" in onchain.details
    assert "fallback_activated=" in onchain.details
    assert 0.0 <= onchain.confidence <= 1.0
    delivery = next(item for item in snapshot.providers if item.provider == "delivery")
    assert "recovery_slo_status" in delivery.details

    assert snapshot.recovery_slo.status in {"healthy", "degraded", "critical"}
    assert "signals" in snapshot.recovery_slo.model_dump()
    assert snapshot.runtime_severity.level in {"ok", "warning", "critical"}
    assert "dimensions" in snapshot.runtime_severity.model_dump()
    assert snapshot.degraded_mode.active is True
    assert "chain_state" in snapshot.degraded_mode.component_states
    assert snapshot.operational_evidence.packet_type == "operational_runtime_evidence"
    assert snapshot.operational_evidence.runtime_state in {"nominal", "degraded"}
    assert snapshot.operational_evidence.recovery_slo_status in {"healthy", "degraded", "critical"}


def test_operations_snapshot_surfaces_critical_runtime_severity(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    weak_chain = ChainStateEvaluation(
        tip_height=100,
        observed_block_height=100,
        headers_height=100,
        confirmation_depth=1,
        reorg_risk_score=0.9,
        finality_score=0.05,
        finality_band="weak",
        confidence_score=0.3,
        freshness={"source": "provider_fallback", "provider_freshness_band": "very_stale"},
        explainability={"degradation_governance": {"degraded_runtime_state": True, "fallback_activated": True}},
    )
    monkeypatch.setattr(
        "app.services.observability.operations_service.ChainStateService.evaluate",
        lambda self, **kwargs: weak_chain,
    )

    with Session(engine) as db:
        for idx in range(10):
            db.add(JobRun(task_name=f"task-{idx}", status="failed", error_message="boom"))
        for idx in range(6):
            db.add(
                DeliveryLog(
                    signal_id=None,
                    channel_type="telegram",
                    destination=f"ops-{idx}",
                    delivery_status="failed",
                    error_message="send failure",
                )
            )
        db.commit()
        snapshot = OperationsSnapshotService().snapshot(db=db)

    assert snapshot.runtime_severity.level == "critical"
    assert snapshot.runtime_severity.escalation_required is True
    assert snapshot.runtime_severity.dimensions["provider_failure"] == "critical"
    assert snapshot.runtime_severity.dimensions["chain_state_degradation"] == "critical"
    assert snapshot.runtime_severity.operator_guidance
    assert snapshot.degraded_mode.active is True
    assert "partial_provider_outage" in snapshot.degraded_mode.reasons
    assert snapshot.degraded_mode.confidence_penalty > 0
    assert snapshot.operational_evidence.degraded_dependencies
    assert snapshot.operational_evidence.unresolved_critical_findings >= 0

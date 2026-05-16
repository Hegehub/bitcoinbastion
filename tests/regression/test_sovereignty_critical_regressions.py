from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user
from app.db.base import Base
from app.db.models.delivery import DeliveryLog
from app.db.models.job_run import JobRun
from app.main import app
from app.schemas.policy import PolicyCheckRequest
from app.services.blockchain.chain_state_service import ChainStateService
from app.services.citadel.citadel_assessment_service import CitadelAssessmentService
from app.services.citadel.disaster_simulation_service import DisasterSimulationService
from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord
from app.services.citadel.recovery_readiness_engine import RecoveryReadinessEngine
from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService
from app.services.delivery.publish_service import PublishResult, SignalPublishService
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot
from app.services.observability.recovery_service import RecoveryCheckService
from app.services.policy.policy_service import TreasuryPolicyService
from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


class _FakeAdmin:
    id = 1
    is_admin = True
    role = "admin"


def test_regression_citadel_assessment_exposes_explainability_and_quality() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=101)
    assert out.overall_score >= 0
    explainability = out.explainability.model_dump() if hasattr(out.explainability, "model_dump") else out.explainability
    assert explainability["guarantees"]["coverage_score"] > 0
    assert "input_quality" in explainability


def test_regression_sovereignty_graph_and_disaster_simulation_are_deterministic() -> None:
    graph = SovereigntyGraphService().build(owner_id=102, wallet_type="multisig-2of3", has_descriptor=True)
    assert graph["nodes"] and graph["edges"]
    assert isinstance(graph["single_points_of_failure"], list)

    first = DisasterSimulationService().simulate(owner_id=102, scenario_code="weak_finality_stress")
    second = DisasterSimulationService().simulate(owner_id=102, scenario_code="weak_finality_stress")
    assert first["survivability_score"] == second["survivability_score"]
    assert first["critical_failure_points"] == second["critical_failure_points"]


def test_regression_recovery_readiness_flags_stale_or_missing_artifacts() -> None:
    artifacts = [
        RecoveryArtifactRecord(
            label="backup_procedure",
            artifact_type="document",
            source_type="fallback",
            confidence=0.6,
            is_verified=True,
            verification_age_days=120,
            required_for_recovery=True,
        )
    ]
    out = RecoveryReadinessEngine().evaluate(
        artifacts=artifacts,
        has_descriptor=False,
        has_instructions=False,
        human_dependency_score=0.9,
    )
    assert out["recovery_readiness_score"] < 0.8
    assert out["recovery_slo"]["status"] in {"degraded", "critical"}


def test_regression_chain_state_finality_and_confidence_degrade_under_stress() -> None:
    healthy = ChainStateService().evaluate(tip_height=900_010, observed_block_height=900_004, data_source="provider_probe")
    stressed = ChainStateService().evaluate(
        tip_height=900_010,
        observed_block_height=900_009,
        provider_tip_height=900_001,
        provider_confidence=0.4,
        provider_data_age_seconds=1800,
        headers_height=900_014,
        data_source="provider_fallback",
    )
    assert healthy.finality_band in {"moderate", "strong"}
    assert stressed.reorg_risk_score >= healthy.reorg_risk_score
    assert stressed.confidence_score <= healthy.confidence_score


def test_regression_utxo_and_mempool_stress_signals_are_conservative() -> None:
    utxo = UTXOAnalyzerService().analyze(utxo_values_sats=[10_000] * 120)
    assert utxo.wallet_profile == "many_small_utxos"
    assert utxo.high_fee_burden_ratio > 0

    mempool = MempoolAnalyzerService().analyze(
        MempoolSnapshot(
            backlog_tx_count=350_000,
            backlog_vbytes=240_000_000,
            median_fee_rate_sat_vb=55,
            high_priority_fee_rate_sat_vb=150,
            snapshot_age_seconds=900,
        )
    )
    assert mempool.congestion_state == "extreme"
    assert mempool.confidence < 1


def test_regression_policy_checks_block_high_risk_transactions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        out = TreasuryPolicyService().evaluate_and_log(
            db=db,
            payload=PolicyCheckRequest(policy_name="default", wallet_health_score=45, transaction_amount_sats=25_000_000),
        )
        assert out.allowed is False
        assert out.violations


def test_regression_delivery_failure_accounting_and_admin_recovery_check() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        db.add(JobRun(task_name="delivery.publish", status="failed", error_message="forced failure"))
        db.add(
            DeliveryLog(
                signal_id=None,
                channel_type="telegram",
                destination="ops-room",
                delivery_status="failed",
                error_message="forced delivery failure",
                sent_at=datetime.now(UTC),
            )
        )
        db.commit()
        out = RecoveryCheckService().evaluate(db=db)
        assert out.ok is False
        assert out.failed_jobs_24h >= 1
        assert out.failed_deliveries_24h >= 1

    app.dependency_overrides[get_admin_user] = lambda: _FakeAdmin()
    try:
        client = TestClient(app)
        response = client.get("/api/v1/admin/jobs/recovery-check")
        assert response.status_code == 200
        payload = response.json()["data"]
        assert "severity" in payload
        assert "recovery_slo" in payload
    finally:
        app.dependency_overrides.pop(get_admin_user, None)


def test_regression_delivery_publish_failure_path_increments_failed_count() -> None:
    class _SignalRepo:
        class _Signal:
            id = 1
            title = "x"
            severity = "high"
            score = 0.9
            summary = "summary"
            recommendation = "hold"
            confidence = 0.9
            source_refs_json = "[]"
            tags_json = "[]"
            signal_type = "news"

        def unpublished(self, limit: int = 20):
            return [self._Signal()]

        def mark_published(self, signal_id: int):
            return None

    class _DeliveryRepo:
        def __init__(self) -> None:
            self.failed = 0

        def already_sent(self, signal_id: int, destination: str) -> bool:
            return False

        def failed_attempts_and_last_failed_at(self, signal_id: int, destination: str):
            return (0, None)

        def record_sent(self, **kwargs):
            return None

        def record_failed(self, **kwargs):
            self.failed += 1

    class _Client:
        def send_message(self, destination: str, message: str):
            raise RuntimeError("forced send failure")

    
    class _Settings:
        telegram_default_chat_id = "ops-room"
        telegram_bot_token = "token"
        delivery_max_failed_attempts_per_signal_destination = 5
        delivery_retry_cooldown_seconds = 0

    import app.services.delivery.publish_service as publish_module
    original = publish_module.get_settings
    publish_module.get_settings = lambda: _Settings()
    try:
        service = SignalPublishService(signals=_SignalRepo(), deliveries=_DeliveryRepo(), telegram_client=_Client())
        out: PublishResult = service.publish_pending_with_stats(limit=1)
    finally:
        publish_module.get_settings = original
    assert out.failed == 1
    assert out.published == 0

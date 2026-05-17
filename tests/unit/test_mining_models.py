from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.mining import (
    MiningCensorshipRisk,
    MiningPool,
    MiningPoolEndpoint,
    MiningSignal,
    PoolSovereigntyScore,
    StratumV2Capability,
    TemplateControlAssessment,
)


def test_mining_models_persist_core_records() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(UTC)

    with Session(engine) as db:
        pool = MiningPool(pool_key="pool-1", display_name="Pool One", source_type="unknown", is_verified=False)
        db.add(pool)
        db.commit()
        db.refresh(pool)

        endpoint = MiningPoolEndpoint(
            pool_id=pool.id,
            endpoint_type="api",
            endpoint_url="https://example.invalid/api",
            source_type="unknown",
            is_verified=False,
            observed_at=now,
        )
        db.add(endpoint)

        sv2 = StratumV2Capability(
            pool_id=pool.id,
            capability_state="claimed_unverified",
            job_declaration_state="unknown",
            source_type="unknown",
            confidence_score=0.33,
            observed_at=now,
        )
        db.add(sv2)

        score = PoolSovereigntyScore(
            pool_id=pool.id,
            score_100=64.5,
            severity="medium",
            source_type="fallback",
            confidence_score=0.44,
            is_verified=False,
            is_fallback=True,
        )
        db.add(score)

        risk = MiningCensorshipRisk(
            pool_id=pool.id,
            risk_score_100=41.0,
            risk_level="medium",
            source_type="unknown",
            confidence_score=0.4,
        )
        db.add(risk)

        template = TemplateControlAssessment(
            pool_id=pool.id,
            template_control_state="shared_control_partial",
            template_control_owner="shared",
            template_sovereignty_score_100=51.0,
            template_interference_risk_score_100=49.0,
            mitm_risk_level="unknown",
            source_type="unknown",
            confidence_score=0.35,
            is_verified=False,
        )
        db.add(template)

        signal = MiningSignal(
            pool_id=pool.id,
            signal_type="TEMPLATE_CONTROL_RISK",
            severity="high",
            source_type="unknown",
            confidence_score=0.52,
            is_verified=False,
            observed_at=now,
        )
        db.add(signal)

        db.commit()

        assert db.query(MiningPool).count() == 1
        assert db.query(MiningPoolEndpoint).count() == 1
        assert db.query(StratumV2Capability).count() == 1
        assert db.query(PoolSovereigntyScore).count() == 1
        assert db.query(MiningCensorshipRisk).count() == 1
        assert db.query(TemplateControlAssessment).count() == 1
        assert db.query(MiningSignal).count() == 1

        loaded_pool = db.query(MiningPool).first()
        assert loaded_pool is not None
        assert loaded_pool.source_type == "unknown"
        assert loaded_pool.is_verified is False

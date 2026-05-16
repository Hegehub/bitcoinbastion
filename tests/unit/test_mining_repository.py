from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.mining import MiningPoolEndpoint
from app.db.repositories.mining_repository import MiningRepository
from tests.fixtures.mining import mining_pool_fixtures


def test_mining_repository_end_to_end_and_latest_ordering() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(UTC)

    with Session(engine) as db:
        repo = MiningRepository(db)

        pool = repo.upsert_pool(
            pool_key="pool-1",
            display_name="Pool One",
            provider_name="provider-a",
            source_type="unknown",
            confidence_score=0.2,
            is_verified=False,
        )
        assert pool.id > 0

        assert repo.get_pool(pool.id) is not None
        assert repo.get_pool_by_name("Pool One") is not None

        endpoint_old = MiningPoolEndpoint(
            pool_id=pool.id,
            endpoint_type="api",
            endpoint_url="https://example.invalid/old",
            observed_at=now - timedelta(hours=2),
        )
        endpoint_new = MiningPoolEndpoint(
            pool_id=pool.id,
            endpoint_type="api",
            endpoint_url="https://example.invalid/new",
            observed_at=now,
        )
        db.add(endpoint_old)
        db.add(endpoint_new)
        db.commit()

        endpoints = repo.list_pool_endpoints(pool.id)
        assert len(endpoints) == 2
        assert endpoints[0].id > endpoints[1].id

        cap = repo.upsert_stratum_v2_capability(
            pool_id=pool.id,
            capability_state="unknown",
            job_declaration_state="claimed_unverified",
            source_type="unknown",
            confidence_score=0.3,
            observed_at=now,
        )
        assert cap.pool_id == pool.id

        older_score = repo.save_pool_score(
            pool_id=pool.id,
            score_100=35.0,
            severity="high",
            source_type="fallback",
            confidence_score=0.25,
            is_fallback=True,
            window_start=now - timedelta(days=2),
            window_end=now - timedelta(days=1),
        )
        newer_score = repo.save_pool_score(
            pool_id=pool.id,
            score_100=55.0,
            severity="medium",
            source_type="unknown",
            confidence_score=0.5,
            window_start=now - timedelta(hours=3),
            window_end=now - timedelta(hours=1),
        )
        latest_score = repo.latest_pool_score(pool.id)
        assert latest_score is not None
        assert latest_score.id == newer_score.id
        assert older_score.id != newer_score.id

        older_risk = repo.save_censorship_risk(
            pool_id=pool.id,
            risk_score_100=70.0,
            risk_level="high",
            window_start=now - timedelta(days=2),
            window_end=now - timedelta(days=1),
        )
        newer_risk = repo.save_censorship_risk(
            pool_id=pool.id,
            risk_score_100=45.0,
            risk_level="medium",
            window_start=now - timedelta(hours=4),
            window_end=now - timedelta(hours=2),
        )
        latest_risk = repo.latest_censorship_risk(pool.id)
        assert latest_risk is not None
        assert latest_risk.id == newer_risk.id
        assert older_risk.id != newer_risk.id

        older_template = repo.save_template_control_assessment(
            pool_id=pool.id,
            template_control_state="pool_controlled",
            observed_at=now - timedelta(hours=3),
        )
        newer_template = repo.save_template_control_assessment(
            pool_id=pool.id,
            template_control_state="shared_control_partial",
            observed_at=now,
        )
        latest_template = repo.latest_template_control_assessment(pool.id)
        assert latest_template is not None
        assert latest_template.id == newer_template.id
        assert older_template.id != newer_template.id

        repo.save_mining_signal(
            pool_id=pool.id,
            signal_type="POOL_CENSORSHIP_RISK",
            severity="high",
            observed_at=now,
            source_type="unknown",
            confidence_score=0.42,
            is_verified=False,
        )
        repo.save_mining_signal(
            pool_id=None,
            signal_type="MINING_PROVIDER_DEGRADATION",
            severity="medium",
            observed_at=now + timedelta(seconds=1),
            source_type="fallback",
            confidence_score=0.31,
            is_fallback=True,
        )

        signals_all = repo.list_mining_signals(limit=10, offset=0)
        assert len(signals_all) == 2
        assert signals_all[0].id > signals_all[1].id

        signals_by_pool = repo.list_mining_signals(pool_id=pool.id, limit=10, offset=0)
        assert len(signals_by_pool) == 1

        signals_by_type = repo.list_mining_signals(
            signal_type="MINING_PROVIDER_DEGRADATION", limit=10, offset=0
        )
        assert len(signals_by_type) == 1

        pools = repo.list_pools(limit=10, offset=0)
        assert len(pools) == 1


def test_mining_repository_accepts_synthetic_fixture_pools() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repo = MiningRepository(db)
        for item in mining_pool_fixtures():
            row = repo.upsert_pool(
                pool_key=item.pool_key,
                display_name=item.display_name,
                provider_name=item.provider_name,
                source_type=str(item.source_quality["source_type"]),
                confidence_score=float(item.source_quality["confidence"]),
                is_verified=bool(item.source_quality["is_verified"]),
                is_fallback=bool(item.source_quality["is_fallback"]),
                is_synthetic=bool(item.source_quality["is_synthetic"]),
                limitations=list(item.source_quality["limitations"]),
                evidence_refs=list(item.source_quality["evidence_refs"]),
            )
            assert row.is_synthetic is True
            assert row.is_verified is False

        pools = repo.list_pools(limit=10, offset=0)
        assert len(pools) == 4

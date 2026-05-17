from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.repositories.mining_repository import MiningRepository
from app.services.mining.stratum_v2_capability_service import StratumV2CapabilityService


def test_adoption_summary_empty_registry() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        service = StratumV2CapabilityService(MiningRepository(db))
        summary = service.summarize_adoption()
        assert summary.total_pools == 0
        assert summary.adoption_rate == 0.0


def test_adoption_summary_mixed_registry() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        repo = MiningRepository(db)
        p1 = repo.upsert_pool(pool_key="pool-a", display_name="Pool A")
        p2 = repo.upsert_pool(pool_key="pool-b", display_name="Pool B")
        p3 = repo.upsert_pool(pool_key="pool-c", display_name="Pool C")
        repo.upsert_pool(pool_key="pool-d", display_name="Pool D")
        repo.save_stratum_v2_capability(
            pool_id=p1.id, capability_state="verified", job_declaration_state="supported", translator_proxy_state="supported", confidence_score=0.9
        )
        repo.save_stratum_v2_capability(
            pool_id=p2.id, capability_state="claimed_unverified", job_declaration_state="claimed_unverified", translator_proxy_state="unknown", confidence_score=0.6
        )
        repo.save_stratum_v2_capability(
            pool_id=p3.id, capability_state="unknown", job_declaration_state="unknown", translator_proxy_state="unknown", confidence_score=0.2
        )
        # p4 intentionally without snapshot
        summary = StratumV2CapabilityService(repo).summarize_adoption()
        assert summary.total_pools == 4
        assert summary.sv2_supported_count == 1
        assert summary.claimed_unverified_count == 1
        assert summary.unknown_count >= 1
        assert summary.adoption_rate == 0.25


def test_adoption_summary_all_unknown() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        repo = MiningRepository(db)
        p1 = repo.upsert_pool(pool_key="u1", display_name="U1")
        p2 = repo.upsert_pool(pool_key="u2", display_name="U2")
        repo.save_stratum_v2_capability(pool_id=p1.id, capability_state="unknown", job_declaration_state="unknown")
        repo.save_stratum_v2_capability(pool_id=p2.id, capability_state="unknown", job_declaration_state="unknown")
        summary = StratumV2CapabilityService(repo).summarize_adoption()
        assert summary.sv2_supported_count == 0
        assert summary.unknown_count == 2
        assert summary.adoption_rate == 0.0


def test_adoption_summary_all_verified() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        repo = MiningRepository(db)
        p1 = repo.upsert_pool(pool_key="v1", display_name="V1")
        p2 = repo.upsert_pool(pool_key="v2", display_name="V2")
        for p in (p1, p2):
            repo.save_stratum_v2_capability(
                pool_id=p.id,
                capability_state="verified",
                job_declaration_state="verified",
                translator_proxy_state="verified",
                confidence_score=0.95,
            )
        summary = StratumV2CapabilityService(repo).summarize_adoption()
        assert summary.total_pools == 2
        assert summary.sv2_supported_count == 2
        assert summary.job_declaration_supported_count == 2
        assert summary.template_control_supported_count == 2
        assert summary.adoption_rate == 1.0

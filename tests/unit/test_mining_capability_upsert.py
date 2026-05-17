from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.mining import MiningPool, MiningPoolEndpoint, StratumV2Capability
from app.db.repositories.mining_repository import MiningRepository
from app.services.mining.pool_registry_service import MiningPoolRegistryService


def test_capability_upsert_is_idempotent_for_pool_and_endpoint() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    service_record = {
        "pool_name": "Case Sensitive Pool",
        "provider_name": "manual_pool_metadata_provider",
        "source_type": "manual_entry",
        "confidence": 0.42,
        "freshness": 1200,
        "is_verified": False,
        "is_synthetic": False,
        "evidence_refs": ["catalog:test"],
        "limitations": ["manual claim"],
        "capability_claims": {
            "supports_stratum_v2": "claimed_unverified",
            "supports_job_declaration": "unknown",
            "supports_translator_proxy": "supported",
            "supports_encrypted_channel": "unsupported",
        },
        "endpoints": [
            {
                "endpoint_type": "stratum",
                "endpoint_url": "stratum+tcp://pool.example:3333",
                "network": "mainnet",
                "source_type": "manual_entry",
            }
        ],
    }

    with Session(engine) as db:
        service = MiningPoolRegistryService(MiningRepository(db))
        first = service.upsert_pool_capability_metadata(service_record)
        second = service.upsert_pool_capability_metadata({**service_record, "pool_name": "case sensitive pool"})

        assert first["pool_id"] == second["pool_id"]
        assert db.query(MiningPool).count() == 1
        assert db.query(MiningPoolEndpoint).count() == 1
        assert db.query(StratumV2Capability).count() == 1


def test_capability_upsert_preserves_history_when_capability_changes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        service = MiningPoolRegistryService(MiningRepository(db))
        base = {
            "pool_name": "History Pool",
            "provider_name": "manual_pool_metadata_provider",
            "source_type": "manual_entry",
            "confidence": 0.5,
            "freshness": 600,
            "evidence_refs": [],
            "limitations": ["manual data"],
            "capability_claims": {
                "supports_stratum_v2": "claimed_unverified",
                "supports_job_declaration": "unknown",
                "supports_translator_proxy": "unknown",
                "supports_encrypted_channel": "unknown",
            },
        }
        service.upsert_pool_capability_metadata(base)
        service.upsert_pool_capability_metadata(
            {
                **base,
                "capability_claims": {
                    "supports_stratum_v2": "supported",
                    "supports_job_declaration": "supported",
                    "supports_translator_proxy": "supported",
                    "supports_encrypted_channel": "supported",
                },
            }
        )

        assert db.query(MiningPool).count() == 1
        assert db.query(StratumV2Capability).count() == 2

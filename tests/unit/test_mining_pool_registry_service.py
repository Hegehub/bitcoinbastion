import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.repositories.mining_repository import MiningRepository
from app.schemas.mining import MiningPoolEndpointCreate, MiningPoolRegistryMetadata
from app.services.mining.pool_registry_service import MiningPoolRegistryService


def test_pool_registry_service_create_list_get_update_and_unknown_metadata() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = MiningPoolRegistryService(MiningRepository(db))

        created = service.register_pool(
            MiningPoolRegistryMetadata(
                pool_name="Pool Registry One",
                website_url="https://pool.example",
                operator_name="Operator One",
                country="US",
                public_documentation_url="https://pool.example/docs",
                notes="Unverified listing",
                source_quality="unknown",
                confidence=0.4,
                freshness=1800,
                extra_tag="third_party_catalog",
            )
        )
        assert created.id > 0
        assert created.display_name == "Pool Registry One"
        assert created.pool_key == "pool-registry-one"

        listed = service.list_pools(limit=10, offset=0)
        assert len(listed) == 1

        loaded_by_id = service.get_pool_by_id(created.id)
        assert loaded_by_id is not None
        loaded_by_name = service.get_pool_by_name("Pool Registry One")
        assert loaded_by_name is not None

        updated = service.update_pool_metadata(
            created.id,
            MiningPoolRegistryMetadata(
                pool_name="Pool Registry One",
                website_url="https://pool.example/v2",
                operator_name="Operator One",
                country="US",
                jurisdiction="Nevada",
                public_documentation_url="https://pool.example/docs-v2",
                notes="Still unverified",
                source_quality="unknown",
                confidence=0.45,
                freshness=1200,
                reviewer_notes={"status": "pending"},
            ),
        )
        assert updated is not None
        metadata = json.loads(updated.metadata_json)
        assert metadata["website_url"] == "https://pool.example/v2"
        assert metadata["reviewer_notes"]["status"] == "pending"

        marked = service.set_pool_active(created.id, is_active=False)
        assert marked is not None
        marked_metadata = json.loads(marked.metadata_json)
        assert marked_metadata["is_active"] is False


def test_pool_registry_service_attaches_endpoints() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = MiningPoolRegistryService(MiningRepository(db))
        created = service.register_pool(
            MiningPoolRegistryMetadata(pool_name="Pool Endpoints", source_quality="unknown", confidence=0.2)
        )

        attached = service.attach_endpoints(
            created.id,
            [
                MiningPoolEndpointCreate(
                    endpoint_type="stratum",
                    endpoint_url="stratum+tcp://pool.example:3333",
                    network="mainnet",
                    source_type="unknown",
                    confidence=0.3,
                    freshness=300,
                    limitations=["unverified"],
                    evidence_refs=["catalog:alpha"],
                ),
                MiningPoolEndpointCreate(
                    endpoint_type="api",
                    endpoint_url="https://pool.example/api",
                    network="mainnet",
                ),
            ],
        )

        assert len(attached) == 2
        assert attached[0].pool_id == created.id
        assert attached[0].endpoint_type == "stratum"

        listed = service.repository.list_pool_endpoints(created.id)
        assert len(listed) == 2

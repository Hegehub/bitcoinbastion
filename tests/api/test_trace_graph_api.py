from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import ChainEvent
from app.main import app
from app.services.bastion_trace.trace_service import TraceService
from app.services.bitcoin_observations.producer import BitcoinObservationProducer
from tests.helpers.access import ACCESS_HEADERS, proof_of_access_overrides
from datetime import UTC, datetime, timedelta

_VALID_ADDRESS = "bc1qexampleaddress0000000000000000000000000"


def _client_with_report() -> tuple[TestClient, Session, int]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    report = TraceService(BastionTraceRepository(session)).analyze_address(_VALID_ADDRESS)

    def override_db() -> Iterator[Session]:
        yield session

    app.dependency_overrides[db_session] = override_db
    assert report.id is not None
    return TestClient(app), session, report.id


def test_trace_graph_snapshot_and_history_retrieval() -> None:
    client, session, report_id = _client_with_report()
    try:
        snapshot = client.get(f"/api/v1/trace/report/{report_id}/graph/snapshot")
        assert snapshot.status_code == 200
        snapshot_data = snapshot.json()["data"]
        assert snapshot_data["snapshot_id"].startswith("trace_snapshot:")
        assert snapshot_data["metadata"]["api_version"] == "trace-graph-api-v1"
        assert snapshot_data["metadata"]["snapshot_version"] == "trace-snapshot-v1"
        assert "layout" not in snapshot_data
        assert snapshot_data["report_fact_ids"]

        history = client.get(f"/api/v1/trace/report/{report_id}/graph/history")
        assert history.status_code == 200
        history_data = history.json()["data"]
        assert history_data["entries"][0]["snapshot_id"] == snapshot_data["snapshot_id"]
        assert history_data["entries"][0]["builder_version"] == "trace-graph-builder-v1"

        snapshot_id = history_data["entries"][0]["snapshot_id"]
        exact = client.get(
            f"/api/v1/trace/report/{report_id}/graph/snapshots/{snapshot_id}"
        )
        assert exact.status_code == 200
        assert exact.json()["data"]["snapshot"]["snapshot_id"] == snapshot_id
        assert client.get(
            f"/api/v1/trace/report/{report_id + 1}/graph/snapshots/{snapshot_id}"
        ).status_code == 404
        assert client.get(
            f"/api/v1/trace/report/{report_id}/graph/snapshots/missing"
        ).status_code == 404
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_trace_graph_object_and_relationship_lookup() -> None:
    client, session, report_id = _client_with_report()
    try:
        snapshot = client.get(f"/api/v1/trace/report/{report_id}/graph/snapshot").json()["data"]
        object_id = snapshot["object_ids"][0]
        relationship_id = snapshot["relationship_ids"][0]

        obj = client.get(f"/api/v1/trace/report/{report_id}/graph/objects/{object_id}")
        assert obj.status_code == 200
        assert obj.json()["data"]["id"] == object_id
        assert obj.json()["data"]["provenance"]["observations"]

        rel = client.get(
            f"/api/v1/trace/report/{report_id}/graph/relationships/{relationship_id}"
        )
        assert rel.status_code == 200
        rel_data = rel.json()["data"]
        assert rel_data["relationship_type"] == "analyzed_as"
        assert rel_data["direction"] == "directed"
        assert rel_data["originating_observation_id"] in snapshot["observation_ids"]
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_trace_graph_openapi_and_generated_transport_contracts() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    path = "/api/v1/trace/report/{report_id}/graph/snapshot"
    operation = schema["paths"][path]["get"]
    assert operation["operationId"] == "get_trace_graph_snapshot_api_v1_trace_report__report_id__graph_snapshot_get"
    assert "TraceGraphSnapshotDTO" in schema["components"]["schemas"]
    assert "TraceGraphError" in schema["components"]["schemas"]

    generated_http = Path("frontend/bastion_ui/transport/generated_http.py").read_text()
    generated_schemas = Path("frontend/bastion_ui/transport/generated_schemas.py").read_text()
    ownership = Path("docs/frontend/migration/01_HTTP_CLIENT_OWNERSHIP_INPUT.json").read_text()
    assert "get_trace_graph_snapshot_api_v1_trace_report__report_id__graph_snapshot_get" in generated_http
    assert "class TraceGraphSnapshotDTO" in generated_schemas
    assert "get_trace_graph_history_api_v1_trace_report__report_id__graph_history_get" in ownership


def test_authoritative_bitcoin_topology_reaches_typed_graph_api_and_history() -> None:
    client, session, report_id = _client_with_report()
    try:
        producer = BitcoinObservationProducer(OnchainRepository(session))
        for index, txid in enumerate(("aa11", "bb22")):
            producer.persist_chain_event(
                ChainEvent(
                    event_type="large_transfer",
                    txid=txid,
                    address=_VALID_ADDRESS,
                    value_sats=10_000 + index,
                    block_height=900001 + index,
                    observed_at=datetime(2026, 8, 14, tzinfo=UTC)
                    + timedelta(minutes=index),
                    payload={
                        "provider": "bitcoin_core_rpc",
                        "source_type": "rpc",
                        "network": "bitcoin-mainnet",
                        "private_provider_token": "must-not-leak",
                    },
                ),
                significance=0.5,
                confidence=0.8,
            )

        response = client.get(f"/api/v1/trace/report/{report_id}/graph/snapshot")
        assert response.status_code == 200
        snapshot = response.json()["data"]
        assert snapshot["topology_snapshot_id"]
        assert snapshot["metadata"]["topology_source_status"] == "authoritative"

        graph_relationships = [
            client.get(
                f"/api/v1/trace/report/{report_id}/graph/relationships/{relationship_id}"
            ).json()["data"]
            for relationship_id in snapshot["relationship_ids"]
        ]
        topology_relationships = [
            item
            for item in graph_relationships
            if item["relationship_type"] == "address_participates_in_transaction"
        ]
        assert len(topology_relationships) == 2
        assert all(item["direction"] == "directed" for item in topology_relationships)
        assert all(item["provenance"]["topology_snapshot_id"] for item in topology_relationships)
        assert "private_provider_token" not in response.text

        history = client.get(f"/api/v1/trace/report/{report_id}/graph/history").json()["data"]
        assert len(history["entries"]) == 2
        assert history["entries"][0]["topology_snapshot_id"] != history["entries"][1][
            "topology_snapshot_id"
        ]

        first_id = history["entries"][0]["snapshot_id"]
        first_before = client.get(
            f"/api/v1/trace/report/{report_id}/graph/snapshots/{first_id}"
        ).json()["data"]
        assert len([
            item for item in first_before["relationships"]
            if item["relationship_type"] == "address_participates_in_transaction"
        ]) == 1
        disagreement = client.get(
            f"/api/v1/trace/report/{report_id}/graph/snapshots/{first_id}/disagreement"
        )
        assert disagreement.status_code == 200
        assert disagreement.json()["data"]["graph_snapshot_id"] == first_id
        assert "TRACE_PRIVACY_CANARY_NEVER_BROWSER" not in disagreement.text
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_proof_packet_is_backend_assembled_typed_and_privacy_safe() -> None:
    client, session, report_id = _client_with_report()
    try:
        BitcoinObservationProducer(OnchainRepository(session)).persist_chain_event(
            ChainEvent(
                event_type="large_transfer",
                txid="proof-packet-tx",
                address=_VALID_ADDRESS,
                value_sats=21_000,
                block_height=900_101,
                observed_at=datetime(2026, 8, 15, tzinfo=UTC),
                payload={
                    "provider": "bitcoin_core_rpc",
                    "source_type": "rpc",
                    "network": "bitcoin-mainnet",
                    "internal_canary": "TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER",
                },
            ),
            significance=0.5,
            confidence=0.8,
        )
        history = client.get(
            f"/api/v1/trace/report/{report_id}/graph/history"
        ).json()["data"]
        snapshot_id = history["entries"][-1]["snapshot_id"]

        with proof_of_access_overrides():
            current = client.get(
                f"/api/v1/trace/report/{report_id}/proof-packet",
                headers=ACCESS_HEADERS,
            )
            historical = client.get(
                f"/api/v1/trace/report/{report_id}/graph/snapshots/{snapshot_id}/proof-packet",
                headers=ACCESS_HEADERS,
            )

        assert current.status_code == historical.status_code == 200
        packet = historical.json()["data"]
        assert packet["graph_snapshot_id"] == snapshot_id
        assert packet["historical"] is True
        assert packet["integrity_status"] == "content_integrity_checked"
        assert packet["verification_status"] == "not_verified"
        assert packet["advisory_only"] is True
        assert packet["evidence"]
        assert any(item["linked_relationship_ids"] for item in packet["evidence"])
        assert all(item["verification_status"] == "not_verified" for item in packet["evidence"])
        assert "raw_content" not in historical.text
        assert "TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER" not in historical.text

        evidence_id = packet["evidence"][0]["evidence_id"]
        workflow_base = f"/api/v1/trace/report/{report_id}/evidence/{evidence_id}"
        params = {"snapshot_id": snapshot_id, "historical": "true"}
        with proof_of_access_overrides():
            lineage = client.get(
                f"{workflow_base}/lineage", params=params, headers=ACCESS_HEADERS
            )
            replay = client.get(
                f"{workflow_base}/replay", params=params, headers=ACCESS_HEADERS
            )
            verification = client.get(
                f"{workflow_base}/verification", params=params, headers=ACCESS_HEADERS
            )
            exported = client.get(
                f"{workflow_base}/export", params=params, headers=ACCESS_HEADERS
            )
        assert lineage.status_code == replay.status_code == verification.status_code == 200
        assert exported.status_code == 200
        assert lineage.json()["data"]["evidence"]["evidence_id"] == evidence_id
        assert lineage.json()["data"]["historical"] is True
        assert replay.json()["data"]["status"] == "match"
        assert verification.json()["data"]["scope"] == "evidence_identity_integrity"
        assert exported.json()["data"]["schema_version"] == "trace-evidence-export-v1"
        combined = lineage.text + replay.text + verification.text + exported.text
        assert "TRACE_EVIDENCE_LINEAGE_PRIVACY_CANARY_NEVER_BROWSER" not in combined
        assert "private_provider_token" not in combined
    finally:
        app.dependency_overrides.clear()
        session.close()

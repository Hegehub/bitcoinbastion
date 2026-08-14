from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.main import app
from app.services.bastion_trace.trace_service import TraceService

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

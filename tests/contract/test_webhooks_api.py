from collections.abc import Generator
from contextlib import contextmanager
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import db_session, get_admin_user
from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.main import app


@contextmanager
def _client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

    def override_db() -> Generator[Session, None, None]:
        with testing_session() as db:
            yield db

    app.dependency_overrides[db_session] = override_db
    app.dependency_overrides[get_admin_user] = lambda: SimpleNamespace(
        id=1, is_admin=True, role="admin"
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _create_payload() -> dict[str, object]:
    return {
        "name": "Ops webhook",
        "target_url": "https://example.com/hooks/bastion",
        "description": "Operator notification endpoint.",
        "event_types": ["signal.created"],
        "metadata": {"team": "ops"},
    }


def test_webhooks_api_lifecycle() -> None:
    with _client() as client:
        created = client.post("/api/v1/webhooks", json=_create_payload())
        assert created.status_code == 201
        created_data = created.json()["data"]
        webhook_id = created_data["id"]
        assert created_data["subscriptions"][0]["event_type"] == "signal.created"
        assert "hmac_secret" not in created.text.lower()
        assert "signing_secret" not in created.text.lower()

        listed = client.get("/api/v1/webhooks")
        assert listed.status_code == 200
        assert listed.json()["data"][0]["id"] == webhook_id

        fetched = client.get(f"/api/v1/webhooks/{webhook_id}")
        assert fetched.status_code == 200
        assert fetched.json()["data"]["id"] == webhook_id

        patched = client.patch(
            f"/api/v1/webhooks/{webhook_id}",
            json={"name": "Trace webhook", "event_types": ["trace.report.created", "webhook.test"]},
        )
        assert patched.status_code == 200
        assert {row["event_type"] for row in patched.json()["data"]["subscriptions"]} == {
            "trace.report.created",
            "webhook.test",
        }

        subscription = client.post(
            f"/api/v1/webhooks/{webhook_id}/subscriptions",
            json={"event_type": "provider.degraded"},
        )
        assert subscription.status_code == 201
        subscriptions = client.get(f"/api/v1/webhooks/{webhook_id}/subscriptions")
        assert subscriptions.status_code == 200
        provider_subscription = next(
            row for row in subscriptions.json()["data"] if row["event_type"] == "provider.degraded"
        )

        deleted_subscription = client.delete(
            f"/api/v1/webhooks/{webhook_id}/subscriptions/{provider_subscription['id']}"
        )
        assert deleted_subscription.status_code == 204

        test_delivery = client.post(
            f"/api/v1/webhooks/{webhook_id}/test", json={"payload": {"ping": "pong"}}
        )
        assert test_delivery.status_code == 200
        test_data = test_delivery.json()["data"]
        assert test_data["status"] == "test_created"
        assert test_data["event_type"] == "webhook.test"
        assert test_data["network_delivery_attempted"] is False
        assert test_data["headers"]["X-Bastion-Event"] == "webhook.test"
        assert test_data["headers"]["X-Bastion-Signature"].startswith("v1=")
        assert test_data["headers"]["X-Bastion-Delivery-ID"] == test_data["delivery_id"]
        assert test_data["request_body_hash"]

        deliveries = client.get(f"/api/v1/webhooks/{webhook_id}/deliveries")
        assert deliveries.status_code == 200
        delivery_row = deliveries.json()["data"][0]
        assert delivery_row["delivery_id"] == test_data["delivery_id"]
        assert delivery_row["attempt_number"] == 1
        assert delivery_row["request_body_hash"] == test_data["request_body_hash"]
        assert "request_headers_json" not in delivery_row
        assert "request_body_json" not in delivery_row
        assert "signing_secret" not in deliveries.text.lower()

        deleted = client.delete(f"/api/v1/webhooks/{webhook_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/v1/webhooks/{webhook_id}").status_code == 404


def test_webhooks_api_rejects_unsafe_and_unknown_inputs() -> None:
    with _client() as client:
        sensitive = client.post(
            "/api/v1/webhooks",
            json=_create_payload() | {"metadata": {"note": "contains private key"}},
        )
        assert sensitive.status_code in {400, 422}

        unknown = client.post(
            "/api/v1/webhooks",
            json=_create_payload() | {"event_types": ["unknown.created"]},
        )
        assert unknown.status_code == 400

        private_url = client.post(
            "/api/v1/webhooks",
            json=_create_payload() | {"target_url": "http://localhost:9000/hook"},
        )
        assert private_url.status_code == 400


def test_webhooks_api_disabled_endpoint_cannot_test_deliver() -> None:
    with _client() as client:
        created = client.post("/api/v1/webhooks", json=_create_payload())
        webhook_id = created.json()["data"]["id"]

        patched = client.patch(f"/api/v1/webhooks/{webhook_id}", json={"enabled": False})
        assert patched.status_code == 200

        test_delivery = client.post(f"/api/v1/webhooks/{webhook_id}/test", json={})
        assert test_delivery.status_code == 400
        assert "disabled" in test_delivery.text.lower()

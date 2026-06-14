from pathlib import Path

import pytest

from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.services.events.webhook_service import WebhookService, WebhookServiceError
from app.services.events.websocket_serialization import serialize_event_payload
from app.plugins.permissions import FORBIDDEN_PERMISSIONS

SENSITIVE_TEXT = "private key xprv wallet.dat seed phrase"


def test_event_payload_sanitizer_rejects_sensitive_material() -> None:
    with pytest.raises(EventPayloadSafetyError):
        assert_event_payload_safe({"value": SENSITIVE_TEXT})


def test_webhook_payload_sanitizer_rejects_sensitive_material() -> None:
    svc = WebhookService.__new__(WebhookService)
    with pytest.raises(WebhookServiceError):
        svc._sanitize_json_object({"value": SENSITIVE_TEXT}, label="payload")


def test_websocket_payload_sanitizer_redacts_sensitive_material() -> None:
    message = serialize_event_payload(
        event_id="evt_1",
        event_type="trace.report.created",
        domain="trace",
        version=1,
        occurred_at=None,
        payload={"value": SENSITIVE_TEXT},
    )
    assert message["payload"]["value"] == "[REDACTED]"
    assert message["metadata"]["redacted"] is True


def test_sdk_examples_do_not_include_sensitive_material() -> None:
    offenders: list[str] = []
    for path in [*Path("sdk/python").rglob("*"), *Path("sdk/typescript/examples").rglob("*")]:
        if path.is_file() and path.suffix in {".py", ".md", ".ts"}:
            text = path.read_text(encoding="utf-8", errors="ignore").casefold()
            if any(term in text for term in ("wallet.dat", "xprv", "private key", "seed phrase")):
                if "never submit" not in text and "reject" not in text:
                    offenders.append(str(path))
    assert offenders == []


def test_plugin_api_permissions_do_not_allow_custody_or_signing() -> None:
    assert "custody:private_key" in FORBIDDEN_PERMISSIONS
    assert "wallet:sign_transaction" in FORBIDDEN_PERMISSIONS
    assert "wallet:broadcast_transaction" in FORBIDDEN_PERMISSIONS

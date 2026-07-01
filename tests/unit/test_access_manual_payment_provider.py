from __future__ import annotations

import logging

import pytest

from app.services.access.payments.base import ManualGrantsDisabledError, PaymentWebhookVerificationError
from app.services.access.payments.manual import ManualGrantProvider


def test_manual_provider_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_ALLOW_MANUAL_GRANTS", raising=False)
    provider = ManualGrantProvider(environment="dev")

    with pytest.raises(ManualGrantsDisabledError):
        provider.create_invoice("lite_pass", 1000, {})


def test_manual_provider_fails_in_production_unless_explicitly_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCESS_ALLOW_MANUAL_GRANTS", "false")
    provider = ManualGrantProvider(environment="production")

    with pytest.raises(ManualGrantsDisabledError):
        provider.create_invoice("lite_pass", 1000, {})


def test_manual_provider_logs_warning_when_enabled_in_production(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)

    ManualGrantProvider(allow_manual_grants=True, environment="production")

    assert "Manual Access grants are enabled" in caplog.text


def test_manual_provider_does_not_support_public_webhook_verification() -> None:
    provider = ManualGrantProvider(allow_manual_grants=True, environment="dev")

    assert provider.verify_webhook(b"{}", {}) is False
    with pytest.raises(PaymentWebhookVerificationError):
        provider.parse_webhook_event(b"{}", {})


def test_manual_provider_does_not_mark_invoices_paid_automatically() -> None:
    provider = ManualGrantProvider(allow_manual_grants=True, environment="dev")
    invoice = provider.create_invoice("lite_pass", 1000, {})
    status = provider.get_invoice_status(invoice.provider_invoice_id)

    assert invoice.status == "pending"
    assert status.settled is False
    assert status.status == "pending"


def test_manual_grant_path_is_tagged_as_manual() -> None:
    provider = ManualGrantProvider(allow_manual_grants=True, environment="dev")
    invoice = provider.create_invoice("lite_pass", 1000, {"safe": "value"})

    assert invoice.provider == "manual"
    assert invoice.provider_invoice_id.startswith("manual-")
    assert invoice.raw_metadata_redacted["grant_type"] == "manual"


def test_manual_grant_redacts_metadata() -> None:
    provider = ManualGrantProvider(allow_manual_grants=True, environment="dev")
    invoice = provider.create_invoice("lite_pass", 1000, {"email": "person@example.invalid", "safe": "value"})

    assert invoice.raw_metadata_redacted["email"] == "[REDACTED]"
    assert invoice.raw_metadata_redacted["safe"] == "value"

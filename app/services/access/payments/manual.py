"""Manual grant payment provider for controlled non-public Access grants."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.access.payments.base import (
    ManualGrantsDisabledError,
    PAYMENT_STATUS_PENDING,
    PaymentProviderInvoice,
    PaymentProviderInvoiceStatus,
    PaymentProviderWebhookEvent,
    PaymentWebhookVerificationError,
)
from app.services.access.payments.redaction import redact_payment_metadata

logger = logging.getLogger(__name__)


class ManualGrantProvider:
    provider_name = "manual"

    def __init__(
        self,
        *,
        allow_manual_grants: bool | None = None,
        environment: str | None = None,
        invoice_ttl_seconds: int = 900,
    ) -> None:
        self.allow_manual_grants = _env_bool("ACCESS_ALLOW_MANUAL_GRANTS", False) if allow_manual_grants is None else allow_manual_grants
        runtime_environment = environment if environment is not None else (os.getenv("ENVIRONMENT") or "dev")
        self.environment = runtime_environment.strip().lower()
        self.invoice_ttl_seconds = invoice_ttl_seconds
        if self.environment in {"prod", "production"} and self.allow_manual_grants:
            logger.warning("Manual Access grants are enabled in a production environment")

    def create_invoice(
        self,
        plan_code: str,
        amount_sats: int,
        metadata: dict[str, Any],
    ) -> PaymentProviderInvoice:
        if not self.allow_manual_grants:
            raise ManualGrantsDisabledError("Manual Access grants are disabled")
        provider_invoice_id = f"manual-{datetime.now(UTC).timestamp():.6f}"
        redacted = redact_payment_metadata({**metadata, "grant_type": "manual"})
        return PaymentProviderInvoice(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            checkout_url=None,
            amount_sats=amount_sats,
            currency="sats",
            status=PAYMENT_STATUS_PENDING,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.invoice_ttl_seconds),
            raw_metadata_redacted=redacted,
        )

    def get_invoice_status(self, provider_invoice_id: str) -> PaymentProviderInvoiceStatus:
        return PaymentProviderInvoiceStatus(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            status=PAYMENT_STATUS_PENDING,
            settled=False,
            expired=False,
            invalid=False,
            checked_at=datetime.now(UTC),
        )

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> bool:
        return False

    def parse_webhook_event(
        self,
        payload: bytes,
        headers: Mapping[str, str],
    ) -> PaymentProviderWebhookEvent:
        raise PaymentWebhookVerificationError("Manual grants do not support payment webhooks")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

"""BTCPay Server payment provider for Bastion Proof-of-Access payments.

This provider creates and verifies payment evidence only. It never issues Access
Certificates, Subscription Entitlements, sessions, or bearer-style credentials.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import httpx

from app.services.access.crypto.hashing import constant_time_equal, hash_canonical_json_prefixed, hmac_sha256_hex
from app.services.access.payments.base import (
    PAYMENT_STATUS_EXPIRED,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PENDING,
    PaymentProviderDisabledError,
    PaymentProviderInvoice,
    PaymentProviderInvoiceStatus,
    PaymentProviderWebhookEvent,
)
from app.services.access.payments.redaction import redact_payment_metadata

logger = logging.getLogger(__name__)

BTCPAY_PROVIDER_NAME = "btcpay"
BTCPAY_STATUS_PROVIDER_UNKNOWN = "provider_unknown"
BTCPAY_STATUS_IGNORED = "ignored"

_SETTLED_STATES = {"settled", "confirmed", "complete", "completed"}
_PENDING_STATES = {"new", "pending", "processing"}
_EXPIRED_STATES = {"expired"}
_INVALID_STATES = {"invalid"}
_SUPPORTED_SETTLED_EVENTS = {
    "invoice settled",
    "invoicesettled",
    "invoice confirmed",
    "invoiceconfirmed",
    "invoice completed",
    "invoicecompleted",
    "invoice payment settled",
    "invoicepaymentsettled",
    "invoice_receivedpayment",
    "invoice receivedpayment",
    "invoice_settled",
    "invoice_confirmed",
    "invoice_completed",
}
_SUPPORTED_EXPIRED_EVENTS = {"invoice expired", "invoiceexpired", "invoice_expired"}
_SUPPORTED_INVALID_EVENTS = {"invoice invalid", "invoiceinvalid", "invoice_invalid"}


class BTCPayConfigError(RuntimeError):
    """Raised when BTCPay configuration is missing or unsafe."""


class BTCPayInvoiceCreateError(RuntimeError):
    """Raised when BTCPay invoice creation fails safely."""


class BTCPayWebhookVerificationError(RuntimeError):
    """Raised when a BTCPay webhook signature cannot be trusted."""


class BTCPayWebhookParseError(RuntimeError):
    """Raised when a BTCPay webhook payload cannot be parsed safely."""


class BTCPayProviderUnavailable(RuntimeError):
    """Raised when BTCPay cannot be reached or returns an unsafe response."""


class BTCPayUnsupportedEvent(RuntimeError):
    """Raised when a BTCPay event is not actionable for Access payments."""


@dataclass(frozen=True, slots=True)
class PaymentProviderHealth:
    provider: str
    enabled: bool
    healthy: bool
    checked_at: datetime
    reason: str | None = None


class BTCPayAccessPaymentProvider:
    """PaymentProvider implementation for BTCPay Server Access invoices."""

    provider_name = BTCPAY_PROVIDER_NAME

    def __init__(
        self,
        *,
        enabled: bool = False,
        base_url: str = "",
        api_key: str = "",
        store_id: str = "",
        webhook_secret: str = "",
        default_currency: str = "BTC",
        checkout_expiry_minutes: int = 30,
        http_timeout_seconds: int = 10,
        webhook_tolerance_seconds: int = 300,
        environment: str = "dev",
        http_client: httpx.Client | None = None,
    ) -> None:
        self.enabled = enabled
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.store_id = store_id
        self.webhook_secret = webhook_secret
        self.default_currency = default_currency
        self.checkout_expiry_minutes = checkout_expiry_minutes
        self.http_timeout_seconds = http_timeout_seconds
        self.webhook_tolerance_seconds = webhook_tolerance_seconds
        self.environment = environment.strip().lower()
        self._http_client = http_client
        self._validate_config()

    def create_invoice(self, plan_code: str, amount_sats: int, metadata: dict[str, Any]) -> PaymentProviderInvoice:
        self._ensure_enabled()
        if amount_sats <= 0:
            raise BTCPayInvoiceCreateError("BTCPay invoice amount must be positive")
        safe_metadata = redact_payment_metadata(
            {
                **metadata,
                "plan_code": plan_code,
                "amount_sats": amount_sats,
                "product": "bastion_access",
                "auth_model": "proof_of_access",
            }
        )
        payload = {
            "amount": _sats_to_btc_string(amount_sats),
            "currency": self.default_currency,
            "metadata": safe_metadata,
            "checkout": {"expirationMinutes": self.checkout_expiry_minutes},
        }
        try:
            response = self._client().post(
                self._invoice_url(),
                json=payload,
                headers={"Authorization": f"token {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("BTCPay invoice creation failed", extra={"provider": self.provider_name})
            raise BTCPayProviderUnavailable("BTCPay invoice creation failed") from exc
        provider_invoice_id = _require_str(data, "id", BTCPayInvoiceCreateError)
        checkout_url = _optional_str(data.get("checkoutLink") or data.get("checkoutUrl") or data.get("url"))
        return PaymentProviderInvoice(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            checkout_url=checkout_url,
            amount_sats=amount_sats,
            currency=str(data.get("currency") or self.default_currency),
            status=_map_provider_status(str(data.get("status") or "new")),
            expires_at=_parse_datetime(data.get("expirationTime") or data.get("expiresAt"))
            or datetime.now(UTC) + timedelta(minutes=self.checkout_expiry_minutes),
            raw_metadata_redacted=redact_payment_metadata(data.get("metadata") if isinstance(data.get("metadata"), dict) else safe_metadata),
        )

    def get_invoice_status(self, provider_invoice_id: str) -> PaymentProviderInvoiceStatus:
        self._ensure_enabled()
        try:
            response = self._client().get(
                f"{self._invoice_url()}/{provider_invoice_id}",
                headers={"Authorization": f"token {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BTCPayProviderUnavailable("BTCPay invoice status unavailable") from exc
        status = _map_provider_status(str(data.get("status") or ""))
        return PaymentProviderInvoiceStatus(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            status=status,
            settled=status == PAYMENT_STATUS_PAID,
            expired=status == PAYMENT_STATUS_EXPIRED,
            invalid=status == PAYMENT_STATUS_FAILED,
            checked_at=datetime.now(UTC),
        )

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> bool:
        if not self.enabled or not self.webhook_secret:
            return False
        signature = _get_header(headers, "btcpay-sig") or _get_header(headers, "x-btcpay-sig")
        if not signature:
            return False
        candidate = signature.strip()
        if candidate.startswith("sha256="):
            candidate = candidate.removeprefix("sha256=")
        if not candidate:
            return False
        expected = hmac_sha256_hex(self.webhook_secret, payload)
        return constant_time_equal(candidate, expected)

    def parse_webhook_event(self, payload: bytes, headers: Mapping[str, str]) -> PaymentProviderWebhookEvent:
        if not self.verify_webhook(payload, headers):
            raise BTCPayWebhookVerificationError("BTCPay webhook signature invalid")
        try:
            data = httpx.Response(200, content=payload).json()
        except ValueError as exc:
            raise BTCPayWebhookParseError("BTCPay webhook payload malformed") from exc
        if not isinstance(data, dict):
            raise BTCPayWebhookParseError("BTCPay webhook payload malformed")
        provider_invoice_id = _extract_invoice_id(data)
        event_type = str(data.get("type") or data.get("eventType") or data.get("name") or "").strip()
        status = _event_status(event_type, data)
        occurred_at = _parse_datetime(data.get("timestamp") or data.get("deliveryTimestamp") or data.get("createdTime")) or datetime.now(UTC)
        if abs((datetime.now(UTC) - occurred_at).total_seconds()) > self.webhook_tolerance_seconds:
            raise BTCPayWebhookVerificationError("BTCPay webhook timestamp outside tolerance")
        redacted_metadata = redact_payment_metadata(_extract_metadata(data))
        event_hash = hash_canonical_json_prefixed(data)
        return PaymentProviderWebhookEvent(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            event_type=event_type or BTCPAY_STATUS_IGNORED,
            status=status,
            settled=status == PAYMENT_STATUS_PAID,
            expired=status == PAYMENT_STATUS_EXPIRED,
            invalid=status == PAYMENT_STATUS_FAILED,
            occurred_at=occurred_at,
            raw_event_hash=str(data.get("id") or data.get("eventId") or event_hash),
            metadata_redacted={**redacted_metadata, "event_hash": event_hash},
        )

    def health_check(self) -> PaymentProviderHealth:
        if not self.enabled:
            return PaymentProviderHealth(self.provider_name, False, False, datetime.now(UTC), "disabled")
        return PaymentProviderHealth(self.provider_name, True, True, datetime.now(UTC))

    def _validate_config(self) -> None:
        if not self.enabled:
            return
        missing = [
            name
            for name, value in {
                "ACCESS_BTCPAY_BASE_URL": self.base_url,
                "ACCESS_BTCPAY_API_KEY": self.api_key,
                "ACCESS_BTCPAY_STORE_ID": self.store_id,
                "ACCESS_BTCPAY_WEBHOOK_SECRET": self.webhook_secret,
            }.items()
            if not value
        ]
        if missing:
            raise BTCPayConfigError("BTCPay provider enabled with missing required configuration")

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise PaymentProviderDisabledError("BTCPay payment provider is disabled")

    def _client(self) -> httpx.Client:
        if self._http_client is not None:
            return self._http_client
        return httpx.Client(timeout=self.http_timeout_seconds)

    def _invoice_url(self) -> str:
        return urljoin(f"{self.base_url}/", f"api/v1/stores/{self.store_id}/invoices")


def _map_provider_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized in _SETTLED_STATES:
        return PAYMENT_STATUS_PAID
    if normalized in _EXPIRED_STATES:
        return PAYMENT_STATUS_EXPIRED
    if normalized in _INVALID_STATES:
        return PAYMENT_STATUS_FAILED
    if normalized in _PENDING_STATES:
        return PAYMENT_STATUS_PENDING
    return BTCPAY_STATUS_PROVIDER_UNKNOWN


def _event_status(event_type: str, data: dict[str, Any]) -> str:
    normalized_event = event_type.strip().lower().replace(".", " ").replace("-", " ")
    if normalized_event in _SUPPORTED_SETTLED_EVENTS:
        return PAYMENT_STATUS_PAID
    if normalized_event in _SUPPORTED_EXPIRED_EVENTS:
        return PAYMENT_STATUS_EXPIRED
    if normalized_event in _SUPPORTED_INVALID_EVENTS:
        return PAYMENT_STATUS_FAILED
    status = _map_provider_status(str(data.get("status") or data.get("invoiceStatus") or ""))
    if status != BTCPAY_STATUS_PROVIDER_UNKNOWN:
        return status
    return BTCPAY_STATUS_IGNORED


def _get_header(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def _extract_invoice_id(data: dict[str, Any]) -> str:
    candidate = data.get("invoiceId") or data.get("invoice_id") or data.get("id")
    invoice = data.get("invoice")
    if candidate is None and isinstance(invoice, dict):
        candidate = invoice.get("id")
    if not isinstance(candidate, str) or not candidate:
        raise BTCPayWebhookParseError("BTCPay webhook missing invoice identifier")
    return candidate


def _extract_metadata(data: dict[str, Any]) -> dict[str, Any]:
    metadata = data.get("metadata")
    invoice = data.get("invoice")
    if not isinstance(metadata, dict) and isinstance(invoice, dict):
        metadata = invoice.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _require_str(data: dict[str, Any], key: str, error_type: type[Exception]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise error_type("BTCPay response missing required field")
    return value


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _sats_to_btc_string(amount_sats: int) -> str:
    whole = amount_sats // 100_000_000
    fraction = amount_sats % 100_000_000
    return f"{whole}.{fraction:08d}".rstrip("0").rstrip(".")

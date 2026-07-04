from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import json
from secrets import token_urlsafe
from time import perf_counter, time
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core import telemetry
from app.db.models.event_outbox import EventOutbox, EventOutboxStatus
from app.db.models.webhooks import WebhookDelivery, WebhookDeliveryStatus, WebhookEndpoint
from app.db.repositories.event_outbox_repository import EventOutboxRepository
from app.db.repositories.webhook_repository import WebhookRepository
from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.services.events.event_serializer import (
    build_webhook_event_envelope,
    serialize_webhook_event_envelope,
)
from app.services.events.webhook_delivery_log_service import WebhookDeliveryLogService
from app.services.events.webhook_signature import build_signed_payload

DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_ATTEMPTS = 8
DEFAULT_INITIAL_RETRY_SECONDS = 30
DEFAULT_MAX_RETRY_SECONDS = 3600


class DeliveryOutcome(StrEnum):
    SUCCESS = "success"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"
    BLOCKED = "blocked"
    NO_SUBSCRIBERS = "no_subscribers"


@dataclass(frozen=True)
class PreparedWebhookDelivery:
    delivery: WebhookDelivery
    raw_body: str
    headers: dict[str, str]


@dataclass(frozen=True)
class WebhookDispatchResult:
    processed: int = 0
    delivered: int = 0
    retrying: int = 0
    dead: int = 0
    blocked: int = 0
    no_subscribers: int = 0


def generate_webhook_secret() -> str:
    return f"whsec_{token_urlsafe(32)}"


def calculate_retry_delay_seconds(
    attempt_number: int,
    *,
    initial_delay_seconds: int = DEFAULT_INITIAL_RETRY_SECONDS,
    max_delay_seconds: int = DEFAULT_MAX_RETRY_SECONDS,
) -> int:
    bounded_attempt = max(attempt_number, 1)
    delay = initial_delay_seconds * (2 ** (bounded_attempt - 1))
    return int(min(delay, max_delay_seconds))


def next_retry_at_for_attempt(
    attempt_number: int,
    *,
    now: datetime | None = None,
    initial_delay_seconds: int = DEFAULT_INITIAL_RETRY_SECONDS,
    max_delay_seconds: int = DEFAULT_MAX_RETRY_SECONDS,
) -> datetime:
    observed = now or datetime.now(timezone.utc)
    return observed + timedelta(
        seconds=calculate_retry_delay_seconds(
            attempt_number,
            initial_delay_seconds=initial_delay_seconds,
            max_delay_seconds=max_delay_seconds,
        )
    )


class WebhookDispatcher:
    """Dispatch event-outbox rows to subscribed webhooks.

    Domain services must publish into the outbox first. This dispatcher is the
    only layer that prepares signed HTTP webhook POST attempts.
    """

    def __init__(
        self,
        db: Session,
        *,
        http_client: httpx.Client | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        initial_retry_seconds: int = DEFAULT_INITIAL_RETRY_SECONDS,
        max_retry_seconds: int = DEFAULT_MAX_RETRY_SECONDS,
    ) -> None:
        self.db = db
        self.delivery_logs = WebhookDeliveryLogService(db)
        self.outbox_repository = EventOutboxRepository(db)
        self.webhook_repository = WebhookRepository(db)
        self.http_client = http_client
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.initial_retry_seconds = initial_retry_seconds
        self.max_retry_seconds = max_retry_seconds

    def prepare_delivery(
        self,
        *,
        endpoint: WebhookEndpoint,
        event_type: str,
        data: dict[str, object],
        limitations: list[str] | None = None,
        event_outbox_id: int | None = None,
        event_id: str | None = None,
        domain: str | None = None,
        payload_version: int = 1,
        status: str = WebhookDeliveryStatus.PENDING.value,
        attempt_number: int = 1,
        now: datetime | None = None,
    ) -> PreparedWebhookDelivery:
        delivery_id = f"whd_{uuid4().hex}"
        observed_at = now or datetime.now(timezone.utc)
        logical_event_id = event_id or str(event_outbox_id or delivery_id)
        envelope = build_webhook_event_envelope(
            event_id=logical_event_id,
            event_type=event_type,
            data=data,
            domain=domain,
            created_at=observed_at,
            payload_version=payload_version,
            limitations=limitations,
        )
        raw_body = serialize_webhook_event_envelope(envelope)
        timestamp = int(observed_at.timestamp() if observed_at.tzinfo else time())
        secret = endpoint.signing_secret or generate_webhook_secret()
        endpoint.signing_secret = secret
        headers = build_signed_payload(
            secret=secret,
            event_type=event_type,
            delivery_id=delivery_id,
            timestamp=timestamp,
            raw_body=raw_body,
            payload_version=payload_version,
            event_id=logical_event_id,
        )
        delivery = self.delivery_logs.create_delivery_attempt(
            endpoint=endpoint,
            event_type=event_type,
            delivery_id=delivery_id,
            raw_body=raw_body,
            headers=headers,
            event_outbox_id=event_outbox_id,
            status=status,
            attempt_number=attempt_number,
            created_at=observed_at,
        )
        return PreparedWebhookDelivery(delivery=delivery, raw_body=raw_body, headers=headers)

    def dispatch_pending_events(
        self, *, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> WebhookDispatchResult:
        processed = delivered = retrying = dead = blocked = no_subscribers = 0
        events = self.outbox_repository.list_pending(limit=batch_size)
        telemetry.BASTION_WEBHOOK_OUTBOX_PENDING_TOTAL.labels(status="pending").set(len(events))
        for item in events:
            result = self.dispatch_outbox_event(item)
            processed += 1
            if result == DeliveryOutcome.SUCCESS:
                delivered += 1
            elif result == DeliveryOutcome.RETRYABLE_FAILURE:
                retrying += 1
            elif result == DeliveryOutcome.TERMINAL_FAILURE:
                dead += 1
            elif result == DeliveryOutcome.BLOCKED:
                blocked += 1
            elif result == DeliveryOutcome.NO_SUBSCRIBERS:
                no_subscribers += 1
        return WebhookDispatchResult(
            processed=processed,
            delivered=delivered,
            retrying=retrying,
            dead=dead,
            blocked=blocked,
            no_subscribers=no_subscribers,
        )

    def dispatch_outbox_event(self, item: EventOutbox) -> DeliveryOutcome:
        if item.status != EventOutboxStatus.PENDING.value:
            return DeliveryOutcome.TERMINAL_FAILURE
        attempt_number = item.attempts + 1
        max_attempts = max(item.max_attempts or self.max_attempts, 1)
        try:
            payload = self._payload_from_outbox(item)
            assert_event_payload_safe(payload)
        except (json.JSONDecodeError, EventPayloadSafetyError, ValueError) as exc:
            self.outbox_repository.mark_dead_letter(item.event_id, _safe_error(exc))
            self._record_metric(item, "blocked")
            return DeliveryOutcome.BLOCKED

        endpoints = self.webhook_repository.list_active_endpoints_for_event(item.event_type)
        if not endpoints:
            self.outbox_repository.mark_dispatched(item.event_id)
            self._record_metric(item, "no_subscribers")
            return DeliveryOutcome.NO_SUBSCRIBERS

        self.outbox_repository.mark_locked(item.event_id, locked_by="webhook_dispatcher")
        any_retryable = False
        all_terminal = True
        for endpoint in endpoints:
            if self.webhook_repository.has_delivered_delivery(endpoint.id, item.id):
                continue
            outcome = self._deliver_to_endpoint(
                item=item,
                endpoint=endpoint,
                payload=payload,
                attempt_number=attempt_number,
            )
            if outcome == DeliveryOutcome.RETRYABLE_FAILURE:
                any_retryable = True
                all_terminal = False
            elif outcome == DeliveryOutcome.SUCCESS:
                continue
            elif outcome == DeliveryOutcome.TERMINAL_FAILURE:
                continue
            elif outcome == DeliveryOutcome.BLOCKED:
                any_retryable = False
                all_terminal = True
                break

        if any_retryable:
            if attempt_number >= max_attempts:
                self.outbox_repository.mark_dead_letter(
                    item.event_id, "Webhook delivery exceeded max retry attempts"
                )
                self._record_metric(item, "dead")
                return DeliveryOutcome.TERMINAL_FAILURE
            retry_at = next_retry_at_for_attempt(
                attempt_number,
                initial_delay_seconds=self.initial_retry_seconds,
                max_delay_seconds=self.max_retry_seconds,
            )
            self.outbox_repository.mark_retry(
                item.event_id,
                "Webhook delivery failed; retry scheduled",
                retry_at,
            )
            self._record_metric(item, "retrying")
            return DeliveryOutcome.RETRYABLE_FAILURE

        if all_terminal:
            self.outbox_repository.mark_dispatched(item.event_id)
            self._record_metric(item, "success")
            return DeliveryOutcome.SUCCESS
        self.outbox_repository.mark_dead_letter(
            item.event_id, "Webhook delivery reached unknown state"
        )
        self._record_metric(item, "dead")
        return DeliveryOutcome.TERMINAL_FAILURE

    def _deliver_to_endpoint(
        self,
        *,
        item: EventOutbox,
        endpoint: WebhookEndpoint,
        payload: dict[str, object],
        attempt_number: int,
    ) -> DeliveryOutcome:
        prepared = self.prepare_delivery(
            endpoint=endpoint,
            event_type=item.event_type,
            data=payload,
            limitations=_limitations_from_payload(payload),
            event_outbox_id=item.id,
            event_id=item.event_id,
            domain=item.domain,
            payload_version=item.event_version,
            attempt_number=attempt_number,
        )
        start = perf_counter()
        client = self.http_client or httpx.Client(
            timeout=self.timeout_seconds, follow_redirects=False
        )
        close_client = self.http_client is None
        try:
            response = client.post(
                endpoint.target_url,
                content=prepared.raw_body,
                headers=prepared.headers,
                timeout=self.timeout_seconds,
            )
            duration_ms = int((perf_counter() - start) * 1000)
            if 200 <= response.status_code < 300:
                self.delivery_logs.mark_delivered(
                    prepared.delivery,
                    response_status_code=response.status_code,
                    response_body=response.text,
                    duration_ms=duration_ms,
                )
                self._record_metric(item, "delivered")
                telemetry.BASTION_WEBHOOK_DISPATCH_LATENCY_SECONDS.labels(
                    event_domain=_event_domain_label(item.domain),
                    event_type_family=_event_type_family(item.event_type),
                    status="success",
                ).observe(duration_ms / 1000)
                return DeliveryOutcome.SUCCESS
            next_retry = None
            status = DeliveryOutcome.TERMINAL_FAILURE
            if response.status_code >= 500:
                status = DeliveryOutcome.RETRYABLE_FAILURE
                next_retry = next_retry_at_for_attempt(
                    attempt_number,
                    initial_delay_seconds=self.initial_retry_seconds,
                    max_delay_seconds=self.max_retry_seconds,
                )
            self.delivery_logs.mark_failed(
                prepared.delivery,
                error_message=f"HTTP {response.status_code}",
                response_status_code=response.status_code,
                response_body=response.text,
                duration_ms=duration_ms,
                next_retry_at=next_retry,
            )
            self._record_metric(item, "failure")
            return status
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            duration_ms = int((perf_counter() - start) * 1000)
            self.delivery_logs.mark_failed(
                prepared.delivery,
                error_message=_safe_error(exc),
                duration_ms=duration_ms,
                next_retry_at=next_retry_at_for_attempt(
                    attempt_number,
                    initial_delay_seconds=self.initial_retry_seconds,
                    max_delay_seconds=self.max_retry_seconds,
                ),
            )
            self._record_metric(item, "failure")
            return DeliveryOutcome.RETRYABLE_FAILURE
        except Exception as exc:  # pragma: no cover - defensive hardening path
            duration_ms = int((perf_counter() - start) * 1000)
            self.delivery_logs.mark_failed(
                prepared.delivery,
                error_message=_safe_error(exc),
                duration_ms=duration_ms,
            )
            self._record_metric(item, "failure")
            return DeliveryOutcome.TERMINAL_FAILURE
        finally:
            if close_client:
                client.close()

    def _payload_from_outbox(self, item: EventOutbox) -> dict[str, object]:
        value = json.loads(item.payload_json or "{}")
        if not isinstance(value, dict):
            raise ValueError("outbox payload is not a JSON object")
        return value

    def _record_metric(self, item: EventOutbox, status: str) -> None:
        labels = {
            "event_domain": _event_domain_label(item.domain),
            "event_type_family": _event_type_family(item.event_type),
            "status": _webhook_metric_status(status),
        }
        telemetry.BASTION_WEBHOOK_DISPATCH_ATTEMPTS_TOTAL.labels(**labels).inc()
        if status in {"success", "delivered", "no_subscribers"}:
            telemetry.BASTION_WEBHOOK_DISPATCH_SUCCESS_TOTAL.labels(**labels).inc()
        elif status == "dead":
            telemetry.BASTION_WEBHOOK_DISPATCH_DEAD_TOTAL.labels(**labels).inc()
        elif status in {"failure", "retrying", "blocked"}:
            telemetry.BASTION_WEBHOOK_DISPATCH_FAILURE_TOTAL.labels(**labels).inc()


def _safe_error(exc: object) -> str:
    text = str(exc) or exc.__class__.__name__
    lowered = text.casefold()
    forbidden = (
        "seed phrase",
        "mnemonic",
        "private key",
        "xprv",
        "yprv",
        "zprv",
        "wallet.dat",
        "keystore",
        "12 words",
        "24 words",
        "signing material",
        "wallet material",
        "sensitive wallet material",
        "secret",
        "token",
    )
    if any(term in lowered for term in forbidden):
        return "[REDACTED]"
    return text[:1000]


def _limitations_from_payload(payload: dict[str, object]) -> list[str]:
    value = payload.get("limitations")
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _event_domain_label(domain: str | None) -> str:
    allowed = {
        "news",
        "event",
        "signal",
        "onchain",
        "trace",
        "wallet",
        "treasury",
        "policy",
        "market",
        "observability",
        "provider",
        "evidence",
        "system",
        "unknown",
    }
    candidate = (domain or "unknown").strip().casefold()
    return candidate if candidate in allowed else "unknown"


def _event_type_family(event_type: str) -> str:
    return _event_domain_label(event_type.split(".", 1)[0] if event_type else "unknown")


def _webhook_metric_status(status: str) -> str:
    allowed = {
        "success",
        "delivered",
        "failure",
        "retrying",
        "dead",
        "blocked",
        "no_subscribers",
        "pending",
        "unknown",
    }
    return status if status in allowed else "unknown"

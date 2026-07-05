import ipaddress
import json
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.time_utils import utcnow
from app.db.models.webhooks import (
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEndpointStatus,
    WebhookEventSubscription,
)
from app.db.repositories.webhook_repository import WebhookRepository, WebhookRepositoryError
from app.events.metadata import sanitize_metadata
from app.events.registry import EVENT_REGISTRY
from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.events.serializer import EventSerializationError, serialize_event_json
from app.events.types import BastionEventType
from app.services.events.webhook_delivery_log_service import request_body_hash
from app.services.events.webhook_dispatcher import WebhookDispatcher, generate_webhook_secret
from app.schemas.webhooks import (
    WebhookEndpointCreate,
    WebhookEndpointOut,
    WebhookEndpointUpdate,
    WebhookSubscriptionOut,
    WebhookTestRequest,
    WebhookTestResponse,
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class WebhookServiceError(ValueError):
    pass


class WebhookNotFoundError(WebhookServiceError):
    pass


class WebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WebhookRepository(db)

    def create_endpoint(
        self, payload: WebhookEndpointCreate, *, created_by: str | int | None = None
    ) -> WebhookEndpoint:
        self._assert_text_safe(payload.name)
        self._assert_text_safe(payload.description)
        target_url = self._validate_target_url(payload.target_url)
        metadata = self._sanitize_json_object(payload.metadata or {}, label="metadata")
        event_types = self._validate_event_types(payload.event_types)
        endpoint = WebhookEndpoint(
            name=payload.name.strip(),
            target_url=target_url,
            description=payload.description,
            enabled=True,
            status=WebhookEndpointStatus.ACTIVE.value,
            created_by=None if created_by is None else str(created_by),
            secret_ref=f"webhook_secret_ref:{uuid4()}",
            signing_secret=generate_webhook_secret(),
            metadata_json=serialize_event_json(metadata),
        )
        try:
            self.repository.create_endpoint(endpoint)
            self.repository.replace_subscriptions(endpoint.id, event_types)
        except WebhookRepositoryError as exc:
            raise WebhookServiceError(str(exc)) from exc
        return endpoint

    def list_endpoints(
        self, *, limit: int = DEFAULT_LIMIT, offset: int = 0
    ) -> list[WebhookEndpoint]:
        return self.repository.list_endpoints(limit=self._limit(limit), offset=max(offset, 0))

    def get_endpoint(self, webhook_id: int) -> WebhookEndpoint:
        endpoint = self.repository.get_endpoint(webhook_id)
        if endpoint is None:
            raise WebhookNotFoundError("Webhook endpoint not found")
        return endpoint

    def update_endpoint(self, webhook_id: int, payload: WebhookEndpointUpdate) -> WebhookEndpoint:
        endpoint = self.get_endpoint(webhook_id)
        if payload.name is not None:
            self._assert_text_safe(payload.name)
            endpoint.name = payload.name.strip()
        if payload.target_url is not None:
            endpoint.target_url = self._validate_target_url(payload.target_url)
        if payload.description is not None:
            self._assert_text_safe(payload.description)
            endpoint.description = payload.description
        if payload.enabled is not None:
            endpoint.enabled = payload.enabled
            if endpoint.status != WebhookEndpointStatus.DELETED.value:
                endpoint.status = (
                    WebhookEndpointStatus.ACTIVE.value
                    if payload.enabled
                    else WebhookEndpointStatus.DISABLED.value
                )
        if payload.metadata is not None:
            metadata = self._sanitize_json_object(payload.metadata, label="metadata")
            endpoint.metadata_json = serialize_event_json(metadata)
        endpoint.updated_at = utcnow()
        try:
            self.repository.update_endpoint(endpoint)
            if payload.event_types is not None:
                self.repository.replace_subscriptions(
                    endpoint.id, self._validate_event_types(payload.event_types)
                )
        except WebhookRepositoryError as exc:
            raise WebhookServiceError(str(exc)) from exc
        return endpoint

    def soft_delete_endpoint(self, webhook_id: int) -> WebhookEndpoint:
        endpoint = self.get_endpoint(webhook_id)
        return self.repository.soft_delete_endpoint(endpoint)

    def add_subscription(self, webhook_id: int, event_type: str) -> WebhookEventSubscription:
        endpoint = self.get_endpoint(webhook_id)
        event_type = self._validate_event_type(event_type)
        existing = self.repository.get_subscription_by_event(endpoint.id, event_type)
        if existing is not None:
            raise WebhookServiceError("Webhook subscription already exists")
        try:
            return self.repository.create_subscription(
                WebhookEventSubscription(webhook_endpoint_id=endpoint.id, event_type=event_type)
            )
        except WebhookRepositoryError as exc:
            raise WebhookServiceError(str(exc)) from exc

    def list_subscriptions(self, webhook_id: int) -> list[WebhookEventSubscription]:
        endpoint = self.get_endpoint(webhook_id)
        return self.repository.list_subscriptions(endpoint.id)

    def remove_subscription(self, webhook_id: int, subscription_id: int) -> None:
        endpoint = self.get_endpoint(webhook_id)
        subscription = self.repository.get_subscription(subscription_id)
        if subscription is None or subscription.webhook_endpoint_id != endpoint.id:
            raise WebhookNotFoundError("Webhook subscription not found")
        self.repository.delete_subscription(subscription)

    def list_deliveries(
        self, webhook_id: int, *, limit: int = DEFAULT_LIMIT, offset: int = 0
    ) -> list[WebhookDelivery]:
        endpoint = self.get_endpoint(webhook_id)
        return self.repository.list_deliveries(
            endpoint.id, limit=self._limit(limit), offset=max(offset, 0)
        )

    def create_test_delivery(
        self, webhook_id: int, payload: WebhookTestRequest
    ) -> WebhookTestResponse:
        endpoint = self.get_endpoint(webhook_id)
        if endpoint.status == WebhookEndpointStatus.DELETED.value:
            raise WebhookNotFoundError("Webhook endpoint not found")
        if not endpoint.enabled or endpoint.status == WebhookEndpointStatus.DISABLED.value:
            raise WebhookServiceError(
                "Webhook endpoint is disabled and cannot receive test deliveries"
            )
        event_type = self._validate_event_type(
            payload.event_type or BastionEventType.WEBHOOK_TEST.value
        )
        if payload.payload is not None:
            self._sanitize_json_object(payload.payload, label="test payload")
        test_payload: dict[str, object] = {
            "message": "Bitcoin Bastion webhook test delivery.",
            "advisory": True,
            "no_custody": True,
        }
        limitations = [
            "Test delivery records are signed and persisted for observability.",
            "Test delivery does not execute transaction signing or custody actions.",
            "Dispatcher retry scheduling is handled by a later prompt.",
        ]
        try:
            prepared = WebhookDispatcher(self.db).prepare_delivery(
                endpoint=endpoint,
                event_type=event_type,
                data=test_payload,
                limitations=limitations,
                status=WebhookDeliveryStatus.TEST_CREATED.value,
                attempt_number=1,
            )
        except (WebhookRepositoryError, ValueError) as exc:
            raise WebhookServiceError(str(exc)) from exc
        return WebhookTestResponse(
            delivery_id=prepared.delivery.delivery_id,
            status=prepared.delivery.status,
            event_type=prepared.delivery.event_type,
            network_delivery_attempted=False,
            headers=prepared.headers,
            request_body_hash=request_body_hash(prepared.raw_body),
        )

    def endpoint_out(self, endpoint: WebhookEndpoint) -> WebhookEndpointOut:
        return WebhookEndpointOut(
            id=endpoint.id,
            name=endpoint.name,
            target_url=endpoint.target_url,
            description=endpoint.description,
            enabled=endpoint.enabled,
            created_by=endpoint.created_by,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at,
            last_delivery_at=endpoint.last_delivery_at,
            failure_count=endpoint.failure_count,
            status=endpoint.status,
            secret_ref=endpoint.secret_ref,
            secret_available=bool(endpoint.signing_secret),
            metadata=self._load_json(endpoint.metadata_json),
            subscriptions=[
                WebhookSubscriptionOut.model_validate(row)
                for row in self.repository.list_subscriptions(endpoint.id)
            ],
        )

    def _validate_event_types(self, event_types: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for event_type in event_types:
            parsed = self._validate_event_type(event_type)
            if parsed in seen:
                continue
            normalized.append(parsed)
            seen.add(parsed)
        if not normalized:
            raise WebhookServiceError("At least one event type is required")
        return normalized

    def _validate_event_type(self, event_type: str) -> str:
        try:
            parsed = BastionEventType(event_type.strip())
        except ValueError as exc:
            raise WebhookServiceError("Unknown webhook event type") from exc
        if parsed not in EVENT_REGISTRY:
            raise WebhookServiceError("Webhook event type is missing registry metadata")
        return parsed.value

    def _validate_target_url(self, target_url: str) -> str:
        candidate = target_url.strip()
        settings = get_settings()
        if not candidate:
            raise WebhookServiceError("Webhook target_url cannot be empty")
        if len(candidate) > 2048:
            raise WebhookServiceError("Webhook target_url exceeds length limit")
        parsed = urlparse(candidate)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
        ):
            raise WebhookServiceError(
                "Webhook target_url must be an http:// or https:// URL without embedded credentials"
            )
        hostname = parsed.hostname
        if hostname is None:
            raise WebhookServiceError("Webhook target_url must include a host")
        lowered_host = hostname.casefold().strip("[]")
        if not settings.webhook_allow_private_network_targets and (
            lowered_host in {"localhost", "localhost.localdomain"}
            or lowered_host.endswith(".local")
        ):
            raise WebhookServiceError(
                "Webhook target_url cannot use localhost or private-network hosts"
            )
        try:
            ip = ipaddress.ip_address(lowered_host)
        except ValueError:
            return candidate
        if not settings.webhook_allow_private_network_targets and (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise WebhookServiceError(
                "Webhook target_url cannot use localhost or private-network hosts"
            )
        return candidate

    def _sanitize_json_object(self, payload: dict[str, object], *, label: str) -> dict[str, object]:
        try:
            assert_event_payload_safe(payload)
            sanitized = sanitize_metadata(payload)
            serialize_event_json(sanitized)
        except (EventPayloadSafetyError, EventSerializationError) as exc:
            raise WebhookServiceError(f"Webhook {label} contains unsafe material") from exc
        return sanitized

    def _assert_text_safe(self, value: str | None) -> None:
        if value is None:
            return
        try:
            assert_event_payload_safe({"text": value})
        except EventPayloadSafetyError as exc:
            raise WebhookServiceError("Webhook text contains unsafe material") from exc

    def _load_json(self, payload: str) -> dict[str, object]:
        try:
            value = json.loads(payload or "{}")
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _limit(self, limit: int) -> int:
        return min(max(limit, 1), MAX_LIMIT)

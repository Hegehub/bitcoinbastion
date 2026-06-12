from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.time_utils import utcnow
from app.db.models.webhooks import (
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointStatus,
    WebhookEventSubscription,
)


class WebhookRepositoryError(ValueError):
    pass


class WebhookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_endpoint(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        self.db.add(endpoint)
        self._flush_safely()
        return endpoint

    def get_endpoint(
        self, webhook_id: int, *, include_deleted: bool = False
    ) -> WebhookEndpoint | None:
        stmt = select(WebhookEndpoint).where(WebhookEndpoint.id == webhook_id)
        if not include_deleted:
            stmt = stmt.where(WebhookEndpoint.status != WebhookEndpointStatus.DELETED.value)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_endpoints(
        self, *, limit: int = 50, offset: int = 0, include_deleted: bool = False
    ) -> list[WebhookEndpoint]:
        stmt = select(WebhookEndpoint)
        if not include_deleted:
            stmt = stmt.where(WebhookEndpoint.status != WebhookEndpointStatus.DELETED.value)
        stmt = (
            stmt.order_by(WebhookEndpoint.created_at.desc(), WebhookEndpoint.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def update_endpoint(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        endpoint.updated_at = utcnow()
        self._flush_safely()
        return endpoint

    def soft_delete_endpoint(self, endpoint: WebhookEndpoint) -> WebhookEndpoint:
        endpoint.enabled = False
        endpoint.status = WebhookEndpointStatus.DELETED.value
        endpoint.updated_at = utcnow()
        self._flush_safely()
        return endpoint

    def create_subscription(
        self, subscription: WebhookEventSubscription
    ) -> WebhookEventSubscription:
        self.db.add(subscription)
        self._flush_safely()
        return subscription

    def get_subscription(self, subscription_id: int) -> WebhookEventSubscription | None:
        return self.db.get(WebhookEventSubscription, subscription_id)

    def get_subscription_by_event(
        self, webhook_id: int, event_type: str
    ) -> WebhookEventSubscription | None:
        stmt = select(WebhookEventSubscription).where(
            WebhookEventSubscription.webhook_endpoint_id == webhook_id,
            WebhookEventSubscription.event_type == event_type,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_subscriptions(self, webhook_id: int) -> list[WebhookEventSubscription]:
        stmt = (
            select(WebhookEventSubscription)
            .where(WebhookEventSubscription.webhook_endpoint_id == webhook_id)
            .order_by(WebhookEventSubscription.created_at.asc(), WebhookEventSubscription.id.asc())
        )
        return list(self.db.execute(stmt).scalars())

    def delete_subscription(self, subscription: WebhookEventSubscription) -> None:
        self.db.delete(subscription)
        self._flush_safely()

    def replace_subscriptions(
        self, webhook_id: int, event_types: list[str]
    ) -> list[WebhookEventSubscription]:
        existing = {row.event_type: row for row in self.list_subscriptions(webhook_id)}
        requested = set(event_types)
        for event_type, row in existing.items():
            if event_type not in requested:
                self.db.delete(row)
        out: list[WebhookEventSubscription] = []
        for event_type in event_types:
            subscription = existing.get(event_type)
            if subscription is None:
                subscription = WebhookEventSubscription(
                    webhook_endpoint_id=webhook_id, event_type=event_type
                )
                self.db.add(subscription)
            else:
                subscription.enabled = True
                subscription.updated_at = utcnow()
            out.append(subscription)
        self._flush_safely()
        return out


    def list_active_endpoints_for_event(self, event_type: str) -> list[WebhookEndpoint]:
        stmt = (
            select(WebhookEndpoint)
            .join(
                WebhookEventSubscription,
                WebhookEventSubscription.webhook_endpoint_id == WebhookEndpoint.id,
            )
            .where(WebhookEventSubscription.event_type == event_type)
            .where(WebhookEventSubscription.enabled.is_(True))
            .where(WebhookEndpoint.enabled.is_(True))
            .where(WebhookEndpoint.status == WebhookEndpointStatus.ACTIVE.value)
            .order_by(WebhookEndpoint.id.asc())
        )
        return list(self.db.execute(stmt).scalars())

    def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self.db.add(delivery)
        self._flush_safely()
        return delivery


    def has_delivered_delivery(self, webhook_endpoint_id: int, event_outbox_id: int) -> bool:
        stmt = select(WebhookDelivery.id).where(
            WebhookDelivery.webhook_endpoint_id == webhook_endpoint_id,
            WebhookDelivery.event_outbox_id == event_outbox_id,
            WebhookDelivery.status == "delivered",
        )
        return self.db.execute(stmt).first() is not None

    def update_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        self._flush_safely()
        return delivery

    def list_deliveries(
        self, webhook_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[WebhookDelivery]:
        stmt = (
            select(WebhookDelivery)
            .where(WebhookDelivery.webhook_endpoint_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc(), WebhookDelivery.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def _flush_safely(self) -> None:
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise WebhookRepositoryError("webhook repository integrity error") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise WebhookRepositoryError("webhook repository error") from exc

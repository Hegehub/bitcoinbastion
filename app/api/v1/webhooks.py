from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_admin_user
from app.api.response_envelope import ok
from app.db.models.auth import User
from app.schemas.webhooks import (
    WebhookEndpointCreate,
    WebhookEndpointUpdate,
    WebhookSubscriptionCreate,
    WebhookSubscriptionOut,
    WebhookTestRequest,
)
from app.services.events.webhook_service import (
    WebhookNotFoundError,
    WebhookService,
    WebhookServiceError,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _service(db: Session) -> WebhookService:
    return WebhookService(db)


def _actor_id(user: User) -> str:
    return str(getattr(user, "id", "operator"))


def _handle_error(exc: WebhookServiceError) -> HTTPException:
    if isinstance(exc, WebhookNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_webhook_endpoint(
    payload: WebhookEndpointCreate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    service = _service(db)
    try:
        endpoint = service.create_endpoint(payload, created_by=_actor_id(current_user))
        db.commit()
        db.refresh(endpoint)
        return ok(service.endpoint_out(endpoint).model_dump(mode="json"))
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.get("")
def list_webhook_endpoints(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    endpoints = service.list_endpoints(limit=limit, offset=offset)
    return ok([service.endpoint_out(endpoint).model_dump(mode="json") for endpoint in endpoints])


@router.get("/{webhook_id}")
def get_webhook_endpoint(
    webhook_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        return ok(service.endpoint_out(service.get_endpoint(webhook_id)).model_dump(mode="json"))
    except WebhookServiceError as exc:
        raise _handle_error(exc) from exc


@router.patch("/{webhook_id}")
def update_webhook_endpoint(
    webhook_id: int,
    payload: WebhookEndpointUpdate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        endpoint = service.update_endpoint(webhook_id, payload)
        db.commit()
        db.refresh(endpoint)
        return ok(service.endpoint_out(endpoint).model_dump(mode="json"))
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.delete("/{webhook_id}")
def delete_webhook_endpoint(
    webhook_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> Response:
    del current_user
    service = _service(db)
    try:
        service.soft_delete_endpoint(webhook_id)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.post("/{webhook_id}/subscriptions", status_code=status.HTTP_201_CREATED)
def create_webhook_subscription(
    webhook_id: int,
    payload: WebhookSubscriptionCreate,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        subscription = service.add_subscription(webhook_id, payload.event_type)
        db.commit()
        db.refresh(subscription)
        return ok(WebhookSubscriptionOut.model_validate(subscription).model_dump(mode="json"))
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.get("/{webhook_id}/subscriptions")
def list_webhook_subscriptions(
    webhook_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        subscriptions = service.list_subscriptions(webhook_id)
        return ok(
            [
                WebhookSubscriptionOut.model_validate(subscription).model_dump(mode="json")
                for subscription in subscriptions
            ]
        )
    except WebhookServiceError as exc:
        raise _handle_error(exc) from exc


@router.delete("/{webhook_id}/subscriptions/{subscription_id}")
def delete_webhook_subscription(
    webhook_id: int,
    subscription_id: int,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> Response:
    del current_user
    service = _service(db)
    try:
        service.remove_subscription(webhook_id, subscription_id)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.post("/{webhook_id}/test")
def create_webhook_test_delivery(
    webhook_id: int,
    payload: WebhookTestRequest,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        result = service.create_test_delivery(webhook_id, payload)
        db.commit()
        return ok(result.model_dump(mode="json"))
    except WebhookServiceError as exc:
        db.rollback()
        raise _handle_error(exc) from exc


@router.get("/{webhook_id}/deliveries")
def list_webhook_deliveries(
    webhook_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(db_session),
    current_user: User = Depends(get_admin_user),
) -> object:
    del current_user
    service = _service(db)
    try:
        deliveries = service.list_deliveries(webhook_id, limit=limit, offset=offset)
        return ok(
            [
                {
                    "id": delivery.id,
                    "delivery_id": delivery.delivery_id,
                    "event_type": delivery.event_type,
                    "status": delivery.status,
                    "attempt_count": delivery.attempt_count,
                    "attempt_number": delivery.attempt_number,
                    "response_status_code": delivery.response_status_code,
                    "error_message": delivery.error_message,
                    "duration_ms": delivery.duration_ms,
                    "request_body_hash": delivery.request_body_hash,
                    "created_at": delivery.created_at.isoformat() if delivery.created_at else None,
                    "next_attempt_at": (
                        delivery.next_attempt_at.isoformat() if delivery.next_attempt_at else None
                    ),
                    "next_retry_at": (
                        delivery.next_retry_at.isoformat() if delivery.next_retry_at else None
                    ),
                    "delivered_at": (
                        delivery.delivered_at.isoformat() if delivery.delivered_at else None
                    ),
                }
                for delivery in deliveries
            ]
        )
    except WebhookServiceError as exc:
        raise _handle_error(exc) from exc

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.events.webhook_dispatcher import WebhookDispatcher
from app.tasks.celery_app import celery_app


@celery_app.task(name="dispatch_webhook_outbox_events")  # type: ignore[untyped-decorator]
def dispatch_webhook_outbox_events(batch_size: int | None = None) -> dict[str, int | str]:
    """Dispatch ready outbox events to subscribed webhook endpoints."""
    settings = get_settings()
    if not settings.webhook_dispatch_enabled:
        return {"status": "disabled", "processed": 0}
    effective_batch_size = batch_size or settings.webhook_dispatch_batch_size
    with SessionLocal() as db:
        result = WebhookDispatcher(
            db,
            timeout_seconds=settings.webhook_dispatch_timeout_seconds,
            max_attempts=settings.webhook_dispatch_max_attempts,
            initial_retry_seconds=settings.webhook_dispatch_initial_retry_seconds,
            max_retry_seconds=settings.webhook_dispatch_max_retry_seconds,
        ).dispatch_pending_events(batch_size=effective_batch_size)
        return {
            "status": "ok",
            "processed": result.processed,
            "delivered": result.delivered,
            "retrying": result.retrying,
            "dead": result.dead,
            "blocked": result.blocked,
            "no_subscribers": result.no_subscribers,
        }

import structlog
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.telemetry import increment_delivery_publish_event
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.delivery.telegram_delivery import (
    TelegramDeliveryClient,
    TelegramDeliveryError,
    TelegramFormatter,
)


@dataclass
class PublishResult:
    published: int
    failed: int
    skipped: int


class SignalPublishService:
    def __init__(
        self,
        signals: SignalRepository,
        deliveries: DeliveryRepository,
        telegram_client: TelegramDeliveryClient | None = None,
    ) -> None:
        self.signals = signals
        self.deliveries = deliveries
        self.telegram_client = telegram_client
        self.logger = structlog.get_logger("signal_publish")

    def publish_pending(self, limit: int = 20) -> int:
        return self.publish_pending_with_stats(limit=limit).published

    def publish_pending_with_stats(self, limit: int = 20) -> PublishResult:
        settings = get_settings()
        pending_signals = self.signals.unpublished(limit=limit)
        destination = settings.telegram_default_chat_id
        if not destination:
            self.logger.warning("signal_publish.skipped_missing_destination")
            increment_delivery_publish_event(status="skipped", reason="missing_destination")
            return PublishResult(published=0, failed=0, skipped=len(pending_signals))
        if not settings.telegram_bot_token:
            self.logger.warning("signal_publish.skipped_missing_bot_token")
            increment_delivery_publish_event(status="skipped", reason="missing_bot_token")
            return PublishResult(published=0, failed=0, skipped=len(pending_signals))

        client = self.telegram_client or TelegramDeliveryClient(settings)
        published = 0
        failed = 0
        skipped = 0

        for signal in pending_signals:
            if self.deliveries.already_sent(signal_id=signal.id, destination=destination):
                increment_delivery_publish_event(status="skipped", reason="duplicate_already_sent")
                self.signals.mark_published(signal.id)
                skipped += 1
                continue

            message = TelegramFormatter.format_signal(signal)
            payload_snapshot = {
                "title": signal.title,
                "severity": signal.severity,
                "score": round(signal.score, 4),
                "message_preview": message[:160],
            }

            try:
                sent = client.send_message(destination=destination, message=message)
                self.deliveries.record_sent(
                    signal_id=signal.id,
                    destination=destination,
                    payload_snapshot=payload_snapshot,
                    provider_message_id=sent.message_id,
                )
                increment_delivery_publish_event(status="sent")
                self.signals.mark_published(signal.id)
                published += 1
            except TelegramDeliveryError as exc:
                self.logger.warning(
                    "signal_publish.delivery_failed",
                    signal_id=signal.id,
                    destination=destination,
                    error=str(exc),
                )
                self.deliveries.record_failed(
                    signal_id=signal.id,
                    destination=destination,
                    payload_snapshot=payload_snapshot,
                    error_message=str(exc),
                )
                increment_delivery_publish_event(status="failed", reason="telegram_delivery_error")
                failed += 1
            except Exception as exc:  # noqa: BLE001
                self.logger.error(
                    "signal_publish.unexpected_failure",
                    signal_id=signal.id,
                    destination=destination,
                    error=str(exc),
                )
                self.deliveries.record_failed(
                    signal_id=signal.id,
                    destination=destination,
                    payload_snapshot=payload_snapshot,
                    error_message=f"unexpected_error: {exc}",
                )
                increment_delivery_publish_event(status="failed", reason="unexpected_exception")
                failed += 1

        return PublishResult(published=published, failed=failed, skipped=skipped)

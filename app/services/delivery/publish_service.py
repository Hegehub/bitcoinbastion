from app.core.config import get_settings
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.delivery.telegram_delivery import TelegramFormatter


class SignalPublishService:
    def __init__(self, signals: SignalRepository, deliveries: DeliveryRepository) -> None:
        self.signals = signals
        self.deliveries = deliveries

    def publish_pending(self, limit: int = 20) -> int:
        settings = get_settings()
        destination = settings.telegram_default_chat_id or "dry-run"
        published = 0

        for signal in self.signals.unpublished(limit=limit):
            if self.deliveries.already_sent(signal_id=signal.id, destination=destination):
                self.signals.mark_published(signal.id)
                continue

            message = TelegramFormatter.format_signal(signal)
            self.deliveries.record_sent(
                signal_id=signal.id,
                destination=destination,
                payload_snapshot={
                    "title": signal.title,
                    "severity": signal.severity,
                    "score": round(signal.score, 4),
                    "message_preview": message[:160],
                },
            )
            self.signals.mark_published(signal.id)
            published += 1

        return published

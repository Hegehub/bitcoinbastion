from app.db.models.signal import Signal
from app.services.delivery.telegram_delivery import TelegramFormatter


def test_signal_formatter_contains_key_fields() -> None:
    signal = Signal(
        signal_type="news",
        severity="high",
        score=0.9,
        confidence=0.8,
        title="Big Bitcoin move",
        summary="Whales moved coins",
    )
    text = TelegramFormatter.format_signal(signal)
    assert "Big Bitcoin move" in text
    assert "Severity" in text

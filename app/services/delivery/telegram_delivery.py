from app.db.models.signal import Signal


class TelegramFormatter:
    @staticmethod
    def format_signal(signal: Signal) -> str:
        return (
            f"🚨 *{signal.title}*\n"
            f"Type: `{signal.signal_type}`\n"
            f"Severity: *{signal.severity}*\n"
            f"Score: *{signal.score:.2f}* | Confidence: *{signal.confidence:.2f}*\n\n"
            f"{signal.summary}"
        )

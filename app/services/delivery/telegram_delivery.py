from app.db.models.signal import Signal


class TelegramFormatter:
    @staticmethod
    def _escape_markdown(text: str) -> str:
        protected = "_[]()~`>#+-=|{}.!"
        escaped = text
        for symbol in protected:
            escaped = escaped.replace(symbol, f"\\{symbol}")
        return escaped

    @classmethod
    def format_signal(cls, signal: Signal) -> str:
        title = cls._escape_markdown(signal.title)
        summary = cls._escape_markdown(signal.summary)
        return (
            f"🚨 *{title}*\n"
            f"Type: `{signal.signal_type}`\n"
            f"Severity: *{signal.severity}*\n"
            f"Score: *{signal.score:.2f}* | Confidence: *{signal.confidence:.2f}*\n\n"
            f"{summary}"
        )

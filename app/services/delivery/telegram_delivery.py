from dataclasses import dataclass
from typing import Callable
import time

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.db.models.signal import Signal


class TelegramDeliveryError(RuntimeError):
    pass


class TelegramDeliveryNonRetryableError(TelegramDeliveryError):
    pass


@dataclass
class TelegramSendResult:
    destination: str
    message_id: str


class TelegramDeliveryClient:
    def __init__(
        self,
        settings: Settings,
        *,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.settings = settings
        self.sleep = sleep or time.sleep

    def send_message(self, *, destination: str, message: str) -> TelegramSendResult:
        if not self.settings.telegram_bot_token:
            raise TelegramDeliveryNonRetryableError("TELEGRAM_BOT_TOKEN is not configured.")
        if not destination:
            raise TelegramDeliveryNonRetryableError("Telegram destination is required.")

        bot_token = self.settings.telegram_bot_token
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": destination,
            "text": message,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }
        retryer = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(min=1, max=8),
            retry=retry_if_exception(
                lambda exc: isinstance(exc, TelegramDeliveryError)
                and not isinstance(exc, TelegramDeliveryNonRetryableError)
            ),
            sleep=self.sleep,
            reraise=True,
        )

        for attempt in retryer:
            with attempt:
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.post(url, json=payload)
                        response.raise_for_status()
                        body = response.json()
                except Exception as exc:  # noqa: BLE001
                    raise TelegramDeliveryError(f"Telegram API request failed: {exc}") from exc

                if not isinstance(body, dict) or not body.get("ok"):
                    description = ""
                    if isinstance(body, dict) and isinstance(body.get("description"), str):
                        description = str(body.get("description"))
                    detail = f" Telegram says: {description}" if description else ""
                    raise TelegramDeliveryError(f"Telegram API returned non-ok response.{detail}")

                result = body.get("result")
                if not isinstance(result, dict):
                    raise TelegramDeliveryError("Telegram API response is missing result payload.")

                message_id = str(result.get("message_id", ""))
                if not message_id:
                    raise TelegramDeliveryError("Telegram API response is missing message_id.")

                return TelegramSendResult(destination=destination, message_id=message_id)

        raise TelegramDeliveryError("Telegram API request exhausted retries without a result.")


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

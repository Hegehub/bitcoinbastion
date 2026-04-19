from typing import Any

import pytest

from app.core.config import get_settings
from app.services.delivery.telegram_delivery import (
    TelegramDeliveryClient,
    TelegramDeliveryError,
    TelegramDeliveryNonRetryableError,
)


class _FakeResponse:
    def __init__(self, *, payload: dict[str, Any], raises_status: bool = False) -> None:
        self._payload = payload
        self._raises_status = raises_status

    def raise_for_status(self) -> None:
        if self._raises_status:
            raise RuntimeError("http status error")

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeHttpClient:
    def __init__(self, *, response: _FakeResponse) -> None:
        self.response = response
        self.post_calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "_FakeHttpClient":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        return None

    def post(self, url: str, json: dict[str, Any]) -> _FakeResponse:
        self.post_calls.append((url, json))
        return self.response


class _FailingHttpClient:
    def __init__(self, counter: dict[str, int]) -> None:
        self.counter = counter

    def __enter__(self) -> "_FailingHttpClient":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        return None

    def post(self, url: str, json: dict[str, Any]) -> _FakeResponse:
        self.counter["calls"] += 1
        return _FakeResponse(payload={"ok": True}, raises_status=True)


def _settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.telegram_bot_token = "unit-test-token"
    settings.telegram_default_chat_id = "@alerts"


def test_send_message_success_returns_provider_message_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _settings()
    fake_http = _FakeHttpClient(response=_FakeResponse(payload={"ok": True, "result": {"message_id": 9988}}))
    monkeypatch.setattr(
        "app.services.delivery.telegram_delivery.httpx.Client",
        lambda timeout: fake_http,
    )

    result = TelegramDeliveryClient(get_settings()).send_message(destination="@alerts", message="hello")

    assert result.destination == "@alerts"
    assert result.message_id == "9988"
    assert len(fake_http.post_calls) == 1
    called_url, called_payload = fake_http.post_calls[0]
    assert "botunit-test-token/sendMessage" in called_url
    assert called_payload["parse_mode"] == "MarkdownV2"


def test_send_message_fails_when_bot_token_missing() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.telegram_bot_token = ""

    with pytest.raises(TelegramDeliveryNonRetryableError, match="TELEGRAM_BOT_TOKEN is not configured"):
        TelegramDeliveryClient(settings).send_message(destination="@alerts", message="hello")


def test_send_message_raises_on_non_ok_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _settings()
    fake_http = _FakeHttpClient(response=_FakeResponse(payload={"ok": False, "description": "blocked"}))
    monkeypatch.setattr(
        "app.services.delivery.telegram_delivery.httpx.Client",
        lambda timeout: fake_http,
    )

    with pytest.raises(TelegramDeliveryError, match="Telegram API returned non-ok response\\. Telegram says: blocked"):
        TelegramDeliveryClient(get_settings(), sleep=lambda _: None).send_message(destination="@alerts", message="hello")


def test_send_message_raises_with_request_context(monkeypatch: pytest.MonkeyPatch) -> None:
    _settings()
    fake_http = _FakeHttpClient(response=_FakeResponse(payload={"ok": True}, raises_status=True))
    monkeypatch.setattr(
        "app.services.delivery.telegram_delivery.httpx.Client",
        lambda timeout: fake_http,
    )

    with pytest.raises(TelegramDeliveryError, match="Telegram API request failed: http status error"):
        TelegramDeliveryClient(get_settings(), sleep=lambda _: None).send_message(destination="@alerts", message="hello")


def test_send_message_retries_transient_request_errors_three_times(monkeypatch: pytest.MonkeyPatch) -> None:
    _settings()
    counter = {"calls": 0}
    monkeypatch.setattr(
        "app.services.delivery.telegram_delivery.httpx.Client",
        lambda timeout: _FailingHttpClient(counter),
    )

    with pytest.raises(TelegramDeliveryError, match="Telegram API request failed: http status error"):
        TelegramDeliveryClient(get_settings(), sleep=lambda _: None).send_message(destination="@alerts", message="hello")

    assert counter["calls"] == 3

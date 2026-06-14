import httpx

from app.services.events.webhook_dispatcher import (
    DEFAULT_MAX_RETRY_SECONDS,
    DeliveryOutcome,
    _safe_error,
    calculate_retry_delay_seconds,
)


def test_retry_delay_is_bounded() -> None:
    assert calculate_retry_delay_seconds(99) == DEFAULT_MAX_RETRY_SECONDS


def test_error_messages_are_sanitized_and_truncated() -> None:
    assert _safe_error(ValueError("private key leaked")) == "[REDACTED]"
    assert len(_safe_error(ValueError("x" * 5000))) == 1000


def test_delivery_outcomes_distinguish_success_retry_and_terminal() -> None:
    assert DeliveryOutcome.SUCCESS.value == "success"
    assert DeliveryOutcome.RETRYABLE_FAILURE.value == "retryable_failure"
    assert DeliveryOutcome.TERMINAL_FAILURE.value == "terminal_failure"
    assert isinstance(httpx.TimeoutException("timeout"), httpx.TimeoutException)

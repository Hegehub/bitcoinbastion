import httpx

from bastion_ui.services.api_client import (
    FALLBACK_MESSAGE,
    INVALID_INPUT_MESSAGE,
    NOT_FOUND_MESSAGE,
    RATE_LIMIT_MESSAGE,
    TIMEOUT_MESSAGE,
    _unwrap_response_envelope,
    normalize_api_error,
)


def test_unwraps_response_envelope_data() -> None:
    assert _unwrap_response_envelope({"data": {"ok": True}}) == {"ok": True}


def test_handles_400_404_422_429() -> None:
    request = httpx.Request("GET", "http://test")
    expected = {
        400: INVALID_INPUT_MESSAGE,
        404: NOT_FOUND_MESSAGE,
        422: INVALID_INPUT_MESSAGE,
        429: RATE_LIMIT_MESSAGE,
    }
    for status, message in expected.items():
        response = httpx.Response(status, request=request)
        assert normalize_api_error(httpx.HTTPStatusError("error", request=request, response=response)) == message


def test_handles_timeout_and_other_without_stack_traces() -> None:
    assert normalize_api_error(httpx.TimeoutException("timeout")) == TIMEOUT_MESSAGE
    message = normalize_api_error(RuntimeError("Traceback: secret stack"))
    assert message == FALLBACK_MESSAGE
    assert "Traceback" not in message

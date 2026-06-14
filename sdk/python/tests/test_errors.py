from __future__ import annotations

import httpx
import pytest

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.errors import (
    BastionAPIError,
    BastionAuthError,
    BastionNotFoundError,
    BastionRateLimitError,
    BastionTimeoutError,
    BastionValidationError,
)


def client_for_status(status_code: int) -> BastionClient:
    return BastionClient(
        base_url="http://example.com",
        transport=httpx.MockTransport(lambda request: httpx.Response(status_code, json={"detail": "error"})),
    )


@pytest.mark.parametrize("status", [400, 422])
def test_validation_errors(status: int) -> None:
    with pytest.raises(BastionValidationError) as exc:
        client_for_status(status).trace.get_report(1)
    assert exc.value.status_code == status


@pytest.mark.parametrize("status", [401, 403])
def test_auth_errors(status: int) -> None:
    with pytest.raises(BastionAuthError):
        client_for_status(status).trace.get_report(1)


def test_not_found_error() -> None:
    with pytest.raises(BastionNotFoundError):
        client_for_status(404).trace.get_report(1)


def test_rate_limit_error() -> None:
    with pytest.raises(BastionRateLimitError):
        client_for_status(429).trace.get_report(1)


def test_api_error() -> None:
    with pytest.raises(BastionAPIError):
        client_for_status(500).trace.get_report(1)


def test_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    client = BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))
    with pytest.raises(BastionTimeoutError):
        client.trace.get_report(1)

from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError

from bastion_ui.transport.foundation import HealthOutDTO, HttpTransport, SafeTransportError
from bastion_ui.transport.generated_foundation import (
    FEATURE_53_FOUNDATION,
    HEALTH_API_V1_HEALTH_GET,
    PUBLIC_STATUS_API_V1_PUBLIC_STATUS_GET,
)


def test_strict_dto_rejects_missing_unknown_and_coerced_fields() -> None:
    with pytest.raises(ValidationError):
        HealthOutDTO.model_validate({"status": "ok"})
    with pytest.raises(ValidationError):
        HealthOutDTO.model_validate({"status": "ok", "app": "bastion", "unknown": 1})
    with pytest.raises(ValidationError):
        HealthOutDTO.model_validate({"status": 1, "app": "bastion"})


def test_feature_53_foundation_has_unique_callable_owners() -> None:
    assert len(FEATURE_53_FOUNDATION) == 2
    assert len({entry.registry_id for entry in FEATURE_53_FOUNDATION}) == 2
    assert len({entry.operation.owner for entry in FEATURE_53_FOUNDATION}) == 2
    assert all(entry.operation.security.public for entry in FEATURE_53_FOUNDATION)


@pytest.mark.asyncio
async def test_callable_transport_validates_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/health"
        return httpx.Response(200, json={"status": "ok", "app": "bitcoin-bastion", "details": {}})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as client:
        result = await HttpTransport(client).invoke(HEALTH_API_V1_HEALTH_GET)
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_malformed_response_fails_without_raw_body() -> None:
    secret = "private_key=never-leak"

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": secret})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as client:
        with pytest.raises(SafeTransportError) as caught:
            await HttpTransport(client).invoke(HEALTH_API_V1_HEALTH_GET)
    assert caught.value.code == "malformed_response"
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403, 404, 409, 422, 429, 500])
async def test_http_errors_are_safe_and_structured(status: int) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="traceback private_key=never-leak")

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as client:
        with pytest.raises(SafeTransportError) as caught:
            await HttpTransport(client).invoke(PUBLIC_STATUS_API_V1_PUBLIC_STATUS_GET)
    assert caught.value.status == status
    assert "private_key" not in str(caught.value)
    assert caught.value.retryable is (status == 429 or status >= 500)


def test_datetime_and_boolean_are_strict() -> None:
    payload = {
        "success": False,
        "data": {
            "platform_status": "degraded",
            "trace_status": "unavailable",
            "production_calibrated": False,
            "modules": {},
            "known_limitations": [],
            "last_update": datetime(2026, 1, 1, tzinfo=UTC),
        },
    }
    result = PUBLIC_STATUS_API_V1_PUBLIC_STATUS_GET.response_type.model_validate(payload)
    assert result.success is False
    assert result.data.modules == {}
    with pytest.raises(ValidationError):
        PUBLIC_STATUS_API_V1_PUBLIC_STATUS_GET.response_type.model_validate(
            {
                "success": False,
                "data": {
                    "platform_status": "degraded",
                    "trace_status": "unavailable",
                    "production_calibrated": 0,
                    "modules": {},
                    "known_limitations": [],
                    "last_update": datetime(2026, 1, 1, tzinfo=UTC),
                },
            }
        )

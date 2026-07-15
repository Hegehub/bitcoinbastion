from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.audit_client import AuditApiClient
from bastion_ui.services.policy_client import PolicyApiClient
from bastion_ui.services.provider_health_client import ProviderHealthApiClient


def _api(handler: Callable[[httpx.Request], httpx.Response]) -> BastionApiClient:
    transport = httpx.MockTransport(handler)
    return BastionApiClient(AppConfig(api_base_url="http://backend.test"), transport=transport)


def test_provider_health_client_handles_missing_endpoint_safely() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "missing"})

        result = await ProviderHealthApiClient(_api(handler)).get_provider_health()
        assert result.ok is False
        assert result.status_code == 404
        assert result.degraded is True
        assert result.error == "The requested resource was not found."

    asyncio.run(run())


def test_policy_client_unwraps_response_envelope() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/trace/report/report-1/policy-facts"
            return httpx.Response(200, json={"data": {"requires_review": True}})

        result = await PolicyApiClient(_api(handler)).get_policy_facts("report-1")
        assert result.ok is True
        assert result.data == {"requires_review": True}

    asyncio.run(run())


def test_audit_client_handles_timeout_without_fake_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow", request=request)

        result = await AuditApiClient(_api(handler)).get_audit_events()
        assert result.ok is False
        assert result.degraded is True
        assert "timed out" in (result.error or "").lower()

    asyncio.run(run())

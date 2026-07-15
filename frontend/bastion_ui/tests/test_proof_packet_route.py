from __future__ import annotations

import pytest

pytest.importorskip("reflex")

import asyncio
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.trace_client import TraceApiClient


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_proof_packet_unavailable_endpoint_is_safe() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing"})

    client = TraceApiClient(
        BastionApiClient(
            config=AppConfig(api_base_url="http://backend.test"),
            transport=httpx.MockTransport(handler),
        )
    )
    result = run(client.get_proof_packet("r1"))
    assert not result.ok
    assert result.status_code == 404
    assert result.error == "The requested resource was not found."


def test_proof_packet_viewer_does_not_define_placeholder_hashes() -> None:
    from bastion_ui.components.trace import proof_packet_viewer

    source = proof_packet_viewer.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read().lower()
    assert "example fingerprint" in text
    assert "fake hash" not in text

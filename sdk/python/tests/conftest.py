from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from bitcoin_bastion_sdk import BastionClient


def json_response(data: Any, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=data)


@pytest.fixture
def captured_requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def client_factory(captured_requests: list[httpx.Request]) -> Callable[[Any], BastionClient]:
    def build(payload: Any) -> BastionClient:
        def handler(request: httpx.Request) -> httpx.Response:
            captured_requests.append(request)
            return json_response(payload)

        return BastionClient(base_url="http://testserver/", transport=httpx.MockTransport(handler))

    return build

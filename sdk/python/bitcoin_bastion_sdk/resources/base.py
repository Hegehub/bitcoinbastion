from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.safety import assert_safe
from bitcoin_bastion_sdk.transport import AsyncBastionTransport, BastionTransport, JsonDict


class BaseResource:
    def __init__(self, transport: BastionTransport) -> None:
        self._transport = transport

    def _get(self, path: str, *, params: JsonDict | None = None, raw: bool = False) -> Any:
        return self._transport.request("GET", path, params=params, raw=raw)

    def _post(self, path: str, *, json: JsonDict | None = None, raw: bool = False) -> Any:
        if json is not None:
            assert_safe(json)
        return self._transport.request("POST", path, json=json, raw=raw)

    def _patch(self, path: str, *, json: JsonDict | None = None, raw: bool = False) -> Any:
        if json is not None:
            assert_safe(json)
        return self._transport.request("PATCH", path, json=json, raw=raw)

    def _delete(self, path: str, *, raw: bool = False) -> Any:
        return self._transport.request("DELETE", path, raw=raw)


class AsyncBaseResource:
    def __init__(self, transport: AsyncBastionTransport) -> None:
        self._transport = transport

    async def _get(self, path: str, *, params: JsonDict | None = None, raw: bool = False) -> Any:
        return await self._transport.request("GET", path, params=params, raw=raw)

    async def _post(self, path: str, *, json: JsonDict | None = None, raw: bool = False) -> Any:
        if json is not None:
            assert_safe(json)
        return await self._transport.request("POST", path, json=json, raw=raw)

    async def _patch(self, path: str, *, json: JsonDict | None = None, raw: bool = False) -> Any:
        if json is not None:
            assert_safe(json)
        return await self._transport.request("PATCH", path, json=json, raw=raw)

    async def _delete(self, path: str, *, raw: bool = False) -> Any:
        return await self._transport.request("DELETE", path, raw=raw)

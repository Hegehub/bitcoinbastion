from __future__ import annotations

import httpx

from bitcoin_bastion_sdk.access_auth import BastionAccessAuth
from bitcoin_bastion_sdk.access.session import BastionPoPSession
from bitcoin_bastion_sdk.auth import AsyncBastionAuth

from bitcoin_bastion_sdk.resources.access import AsyncAccessResource
from bitcoin_bastion_sdk.resources.evidence import AsyncEvidenceResource
from bitcoin_bastion_sdk.resources.health import AsyncHealthResource
from bitcoin_bastion_sdk.resources.market import AsyncMarketResource
from bitcoin_bastion_sdk.resources.news import AsyncNewsResource
from bitcoin_bastion_sdk.resources.onchain import AsyncOnchainResource
from bitcoin_bastion_sdk.resources.policy import AsyncPolicyResource
from bitcoin_bastion_sdk.resources.provider_health import AsyncProviderHealthResource
from bitcoin_bastion_sdk.resources.signals import AsyncSignalsResource
from bitcoin_bastion_sdk.resources.trace import AsyncTraceResource
from bitcoin_bastion_sdk.resources.treasury import AsyncTreasuryResource
from bitcoin_bastion_sdk.resources.wallet import AsyncWalletResource
from bitcoin_bastion_sdk.resources.webhooks import AsyncWebhooksResource
from bitcoin_bastion_sdk.transport import AsyncBastionTransport
from bitcoin_bastion_sdk.websocket import WebSocketClient


class AsyncBastionClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 5.0,
        api_prefix: str = "/api/v1",
        headers: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        access_auth: BastionAccessAuth | None = None,
        pop_session: BastionPoPSession | None = None,
        allow_legacy_bearer_auth: bool = False,
    ) -> None:
        self._transport = AsyncBastionTransport(
            base_url=base_url,
            api_prefix=api_prefix,
            api_key=api_key,
            timeout=timeout,
            headers=headers,
            transport=transport,
            access_auth=access_auth,
            pop_session=pop_session,
            allow_legacy_bearer_auth=allow_legacy_bearer_auth,
        )
        self.access = AsyncAccessResource(self._transport)
        self.auth = AsyncBastionAuth(self._transport)
        self.health = AsyncHealthResource(self._transport)
        self.signals = AsyncSignalsResource(self._transport)
        self.news = AsyncNewsResource(self._transport)
        self.onchain = AsyncOnchainResource(self._transport)
        self.trace = AsyncTraceResource(self._transport)
        self.evidence = AsyncEvidenceResource(self._transport)
        self.market = AsyncMarketResource(self._transport)
        self.treasury = AsyncTreasuryResource(self._transport)
        self.policy = AsyncPolicyResource(self._transport)
        self.wallet = AsyncWalletResource(self._transport)
        self.provider_health = AsyncProviderHealthResource(self._transport)
        self.webhooks = AsyncWebhooksResource(self._transport)
        self.websocket = WebSocketClient(
            base_url=self._transport.config.base_url,
            api_prefix=self._transport.config.api_prefix,
            headers=self._transport.headers,
        )

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> "AsyncBastionClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

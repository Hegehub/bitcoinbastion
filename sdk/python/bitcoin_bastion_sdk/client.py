from __future__ import annotations

import httpx

from bitcoin_bastion_sdk.access_auth import BastionAccessAuth
from bitcoin_bastion_sdk.access.session import BastionPoPSession
from bitcoin_bastion_sdk.auth import BastionAuth

from bitcoin_bastion_sdk.resources.access import AccessResource
from bitcoin_bastion_sdk.resources.evidence import EvidenceResource
from bitcoin_bastion_sdk.resources.health import HealthResource
from bitcoin_bastion_sdk.resources.market import MarketResource
from bitcoin_bastion_sdk.resources.news import NewsResource
from bitcoin_bastion_sdk.resources.onchain import OnchainResource
from bitcoin_bastion_sdk.resources.payregister import PayRegisterLNURLResource
from bitcoin_bastion_sdk.resources.policy import PolicyResource
from bitcoin_bastion_sdk.resources.provider_health import ProviderHealthResource
from bitcoin_bastion_sdk.resources.signals import SignalsResource
from bitcoin_bastion_sdk.resources.trace import TraceResource
from bitcoin_bastion_sdk.resources.treasury import TreasuryResource
from bitcoin_bastion_sdk.resources.wallet import WalletResource
from bitcoin_bastion_sdk.resources.webhooks import WebhooksResource
from bitcoin_bastion_sdk.transport import BastionTransport
from bitcoin_bastion_sdk.websocket import WebSocketClient


class BastionClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 5.0,
        api_prefix: str = "/api/v1",
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        access_auth: BastionAccessAuth | None = None,
        pop_session: BastionPoPSession | None = None,
        allow_legacy_bearer_auth: bool = False,
        self_hosted_mode: bool = False,
        allow_onion: bool = False,
    ) -> None:
        self._transport = BastionTransport(
            base_url=base_url,
            api_prefix=api_prefix,
            api_key=api_key,
            timeout=timeout,
            headers=headers,
            transport=transport,
            access_auth=access_auth,
            pop_session=pop_session,
            allow_legacy_bearer_auth=allow_legacy_bearer_auth,
            self_hosted_mode=self_hosted_mode,
            allow_onion=allow_onion,
        )
        self.access = AccessResource(self._transport)
        self.auth = BastionAuth(self._transport)
        self.health = HealthResource(self._transport)
        self.signals = SignalsResource(self._transport)
        self.news = NewsResource(self._transport)
        self.onchain = OnchainResource(self._transport)
        self.payregister_lnurl = PayRegisterLNURLResource(self._transport)
        self.trace = TraceResource(self._transport)
        self.evidence = EvidenceResource(self._transport)
        self.market = MarketResource(self._transport)
        self.treasury = TreasuryResource(self._transport)
        self.policy = PolicyResource(self._transport)
        self.wallet = WalletResource(self._transport)
        self.provider_health = ProviderHealthResource(self._transport)
        self.webhooks = WebhooksResource(self._transport)
        self.websocket = WebSocketClient(
            base_url=self._transport.config.base_url,
            api_prefix=self._transport.config.api_prefix,
            headers=self._transport.headers,
        )

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "BastionClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

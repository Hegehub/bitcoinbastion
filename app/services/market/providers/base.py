from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.market.schemas import ProviderPrice


class BaseMarketProvider(ABC):
    @abstractmethod
    def fetch_btc_price(self) -> ProviderPrice: ...

    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def healthcheck(self) -> bool: ...

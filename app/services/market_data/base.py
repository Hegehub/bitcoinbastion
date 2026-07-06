from __future__ import annotations
from abc import ABC, abstractmethod
from app.services.market_data.provider_models import NormalizedBTCPricePoint


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_ticker(self) -> NormalizedBTCPricePoint: ...
    @abstractmethod
    def fetch_recent_prices(self) -> list[NormalizedBTCPricePoint]: ...
    @abstractmethod
    def get_provider_name(self) -> str: ...
    @abstractmethod
    def get_provider_metadata(self) -> dict[str, object]: ...

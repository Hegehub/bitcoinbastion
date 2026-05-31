from app.services.market_data.base import MarketDataProvider
from app.services.market_data.providers import BinanceProvider, BitstampProvider, CoinbaseProvider, KrakenProvider


def get_providers() -> list[MarketDataProvider]:
    return [BinanceProvider(), KrakenProvider(), CoinbaseProvider(), BitstampProvider()]

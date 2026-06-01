from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class BTCPricePointSchema(BaseModel):
    provider_name: str
    provider_kind: str
    symbol: str = "BTC"
    pair: str = "BTCUSD"
    price_usd: Decimal
    observed_at: datetime
    provider_confidence: float
    provider_latency_ms: int | None = None
    provider_status: str

class MarketHealthSnapshot(BaseModel):
    provider_count: int
    healthy_provider_count: int
    degraded_provider_count: int
    failed_provider_count: int
    global_market_confidence: float
    median_provider_latency_ms: float
    stale_provider_count: int
    generated_at: datetime

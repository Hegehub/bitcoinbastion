from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ProviderPrice:
    provider: str
    pair: str
    price_usd: float
    observed_at: datetime
    latency_ms: int
    raw_payload: dict[str, object]


@dataclass(slots=True)
class BTCMarketContext:
    median_price_usd: float
    provider_count: int
    aggregation_confidence: float
    provider_spread_pct: float
    providers: list[dict[str, object]] = field(default_factory=list)
    is_degraded: bool = False
    reason: str = ""
    generated_at: datetime | None = None

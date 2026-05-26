from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(slots=True)
class NormalizedBTCPricePoint:
    provider: str
    pair: str
    price_usd: float
    observed_at: datetime
    latency_ms: int
    provider_confidence: float
    raw_payload_hash: str
    metadata_json: dict[str, object] = field(default_factory=dict)

@dataclass(slots=True)
class AggregatedBTCPrice:
    median_price: float
    provider_count: int
    provider_spread_pct: float
    aggregated_confidence: float
    providers_used: list[dict[str, object]]
    degraded_mode: bool
    generated_at: datetime

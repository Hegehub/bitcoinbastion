from __future__ import annotations

from statistics import median


def ohlc(prices: list[float]) -> tuple[float, float, float, float]:
    return prices[0], max(prices), min(prices), prices[-1]


def spread_pct(prices: list[float]) -> float:
    if not prices:
        return 0.0
    med = median(prices)
    if med == 0:
        return 0.0
    return ((max(prices) - min(prices)) / med) * 100

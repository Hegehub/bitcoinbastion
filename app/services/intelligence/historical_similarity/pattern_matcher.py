from __future__ import annotations

from dataclasses import dataclass

from app.db.models.news_event import NewsEvent
from app.services.intelligence.historical_similarity_metrics import PATTERN_MATCH_COUNT
from app.services.intelligence.pattern_library import MarketPattern, infer_pattern_type


@dataclass(frozen=True)
class PatternMatch:
    pattern: str
    score: float
    explanation: str


class PatternMatcher:
    def identify(self, event: NewsEvent) -> list[PatternMatch]:
        primary = infer_pattern_type(event.canonical_title, event.event_type, event.event_category)
        matches = [
            PatternMatch(
                primary.value,
                self._score(primary),
                f"Primary pattern inferred from event title/category: {primary.value}.",
            )
        ]
        text = f"{event.canonical_title} {event.canonical_summary}".lower()
        secondary = {
            MarketPattern.SECURITY_INCIDENT: ["hack", "exploit", "malware"],
            (
                MarketPattern.BANKING_STRESS
                if hasattr(MarketPattern, "BANKING_STRESS")
                else MarketPattern.MACRO_RISK_OFF
            ): ["bank", "liquidity stress"],
            MarketPattern.VOLATILITY_EXPANSION: ["volatility", "liquidation", "cascade"],
        }
        for pattern, keywords in secondary.items():
            if pattern != primary and any(keyword in text for keyword in keywords):
                matches.append(
                    PatternMatch(
                        pattern.value,
                        0.58,
                        f"Secondary pattern matched keyword(s): {', '.join(keywords)}.",
                    )
                )
        PATTERN_MATCH_COUNT.inc(len(matches))
        return sorted(matches, key=lambda item: item.score, reverse=True)

    def _score(self, pattern: MarketPattern) -> float:
        return 0.35 if pattern == MarketPattern.UNKNOWN else 0.86

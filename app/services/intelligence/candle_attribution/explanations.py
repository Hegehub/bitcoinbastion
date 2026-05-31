class CandleAttributionExplanationBuilder:
    def build_summary(self, title: str, timeframe: str, direction_match: bool) -> str:
        match_phrase = "matched" if direction_match else "did not fully match"
        return f"{title} may have contributed to the {timeframe} BTC candle context and {match_phrase} candle direction."

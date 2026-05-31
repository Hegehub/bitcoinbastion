
def classify_market_regime(volatility_score: float, disagreement: float) -> str:
    if volatility_score > 0.85 or disagreement > 0.7:
        return "extreme"
    if volatility_score > 0.65:
        return "shock"
    if volatility_score > 0.4:
        return "volatile"
    if volatility_score > 0.2:
        return "normal"
    return "quiet"

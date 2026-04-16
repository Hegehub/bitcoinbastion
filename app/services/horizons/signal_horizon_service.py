from app.db.models.signal import Signal


class SignalHorizonService:
    """Baseline multi-horizon interpretation for a signal."""

    def build(self, signal: Signal) -> dict[str, float | str]:
        base = signal.score
        confidence = signal.confidence

        short_term = min(1.0, base * 0.8 + confidence * 0.2)
        medium_term = min(1.0, base * 0.6 + confidence * 0.4)
        long_term = min(1.0, base * 0.4 + confidence * 0.6)

        dominant = "short"
        if long_term >= max(short_term, medium_term):
            dominant = "long"
        elif medium_term >= short_term:
            dominant = "medium"

        return {
            "short": round(short_term, 4),
            "medium": round(medium_term, 4),
            "long": round(long_term, 4),
            "dominant": dominant,
        }

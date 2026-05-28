from dataclasses import dataclass


@dataclass
class FalseSignalResult:
    detected: bool
    severity: str
    confidence_penalty: float
    explanation: str


class FalseSignalDetector:
    def detect(self, news_score: float, price_move_strength: float, provider_agreement: float, confirmed_sources: int) -> FalseSignalResult:
        if news_score >= 0.75 and price_move_strength < 0.2 and provider_agreement < 0.5 and confirmed_sources <= 1:
            return FalseSignalResult(True, "high", 0.20, "High-scored news with weak market reaction and weak confirmation.")
        return FalseSignalResult(False, "none", 0.0, "No false-signal pattern detected.")

from .keyword_profiles import KEYWORD_PROFILES


class SentimentEngine:
    labels = ("POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNCERTAIN")

    def _hits(self, text: str, key: str) -> int:
        lowered = text.lower()
        return sum(1 for k in KEYWORD_PROFILES[key] if k in lowered)

    def analyze(self, title: str, summary: str = "", content: str = "") -> tuple[float, str, dict[str, int]]:
        text = f"{title} {summary} {content}"
        pos, neg = self._hits(text, "positive"), self._hits(text, "negative")
        base = max(1, pos + neg)
        score = max(0.0, min(1.0, 0.5 + ((pos - neg) / (2 * base))))
        if pos == 0 and neg == 0:
            label = "UNCERTAIN"
        elif pos > neg * 1.4:
            label = "POSITIVE"
        elif neg > pos * 1.4:
            label = "NEGATIVE"
        elif pos == neg:
            label = "NEUTRAL"
        else:
            label = "MIXED"
        return score, label, {"positive": pos, "negative": neg}

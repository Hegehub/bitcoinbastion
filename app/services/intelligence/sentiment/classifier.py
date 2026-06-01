from .keyword_rules import KEYWORD_RULES


class LocalKeywordClassifier:
    def classify(self, text: str) -> dict[str, int]:
        lowered = text.lower()
        return {k: sum(1 for kw in v if kw in lowered) for k, v in KEYWORD_RULES.items()}

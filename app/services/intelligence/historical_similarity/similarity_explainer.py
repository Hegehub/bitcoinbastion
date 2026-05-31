from __future__ import annotations

from app.services.intelligence.historical_similarity.similarity_scoring import SimilarityScore


class SimilarityExplainer:
    def explain(self, pattern: str, score: SimilarityScore, sample_size: int) -> dict[str, object]:
        reasons = [f"pattern={pattern}", f"similarity_band={score.band}"]
        reasons.extend(f"{key}={value:.2f}" for key, value in score.dimensions.items() if value >= 0.75)
        return {
            "summary": "Evidence-based historical similarity; not a prediction.",
            "reasons": reasons,
            "limitations": self.limitations(score, sample_size),
            "dimension_scores": score.dimensions,
        }

    def limitations(self, score: SimilarityScore, sample_size: int) -> list[str]:
        limitations = [
            "Correlation is not proof of causation.",
            "Historical similarity does not guarantee future outcomes.",
            "This is not financial advice.",
        ]
        if sample_size < 3:
            limitations.append("small sample size")
        if score.dimensions.get("market_regime", 0.0) < 0.75:
            limitations.append("different market regime")
        if score.dimensions.get("source_tier", 0.0) < 0.75:
            limitations.append("low source diversity or provider confidence")
        if score.score < 0.60:
            limitations.append("weak attribution confidence")
        return limitations

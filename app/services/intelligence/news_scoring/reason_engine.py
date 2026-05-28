def build_explanation(scores: dict[str, float]) -> dict[str, str]:
    return {
        "summary": "Correlation is not proof of causation. This analysis is informational and evidence-based, not financial advice.",
        "btc_relevance": f"Bitcoin relevance derived from deterministic keyword and context matching: {scores.get('btc_relevance_score', 0):.2f}",
    }


def build_limitations(provider_confidence: float) -> dict[str, object]:
    limitations = ["Scoring is correlation-based.", "Article coverage may evolve over time."]
    if provider_confidence < 0.5:
        limitations.append("Source confidence reduced due to provider instability.")
    return {"limitations": limitations}

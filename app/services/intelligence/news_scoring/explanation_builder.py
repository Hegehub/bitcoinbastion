def build_explanation(top_factors: list[str]) -> dict[str, object]:
    return {
        "top_factors": top_factors,
        "limitations": [
            "Sentiment classification is keyword-based.",
            "Price impact is not directly computed.",
            "Correlation is not proof of causation.",
        ],
    }

def build_scoring_explanation(
    summary: str, key_factors: list[str], limitations: list[str]
) -> dict[str, object]:
    return {"summary": summary, "key_factors": key_factors, "limitations": limitations}

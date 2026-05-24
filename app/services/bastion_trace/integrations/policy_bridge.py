def recommend(trace_band: str, confidence: float) -> str:
    if trace_band in {"HIGH", "CRITICAL"}:
        return "REQUIRE_MANUAL_REVIEW"
    if trace_band == "UNKNOWN" or confidence < 0.35:
        return "INSUFFICIENT_INFORMATION"
    if trace_band == "MEDIUM":
        return "REQUIRE_MANUAL_REVIEW"
    return "ALLOW_WITH_NOTE"

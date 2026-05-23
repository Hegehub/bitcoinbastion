def merchant_recommendation(trace_band: str) -> str:
    return {"LOW": "ACCEPT_WITH_NORMAL_CAUTION", "MEDIUM": "ACCEPT_WITH_NOTE", "HIGH": "HOLD_FOR_REVIEW", "CRITICAL": "HOLD_FOR_REVIEW"}.get(trace_band, "INSUFFICIENT_INFORMATION")

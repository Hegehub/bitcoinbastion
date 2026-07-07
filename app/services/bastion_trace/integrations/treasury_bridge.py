def treasury_review_level(trace_band: str) -> str:
    return {"CRITICAL": "SENIOR_REVIEW", "HIGH": "MANUAL_REVIEW", "MEDIUM": "LIGHT_REVIEW"}.get(
        trace_band, "NONE"
    )

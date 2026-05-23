def score_impact(trace_band: str, provider_disagreement_severity: str = "NONE") -> int:
    base = {"LOW": -1, "MEDIUM": -3, "HIGH": -8, "CRITICAL": -15, "UNKNOWN": 0}.get(trace_band, 0)
    if provider_disagreement_severity == "HIGH":
        base -= 3
    return base

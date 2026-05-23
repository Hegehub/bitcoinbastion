from app.schemas.bastion_trace import TraceBand


def apply_false_positive_guard(score: float, confidence: float, evidence_count: int, baseline_mode: bool, stale: bool, weak_source: bool) -> tuple[float, list[str]]:
    reasons:list[str]=[]
    if baseline_mode and score>=50:
        score=24
        reasons.append("FALSE_POSITIVE_GUARD_APPLIED")
    if evidence_count<=1 and weak_source and score>=75:
        score=49
        reasons.append("FALSE_POSITIVE_GUARD_APPLIED")
    if stale and evidence_count<=1 and score>=50:
        score=49
        reasons.append("FALSE_POSITIVE_GUARD_APPLIED")
    if confidence<0.5 and score>=75:
        score=74
        reasons.append("FALSE_POSITIVE_GUARD_APPLIED")
    return score, reasons


def score_to_band(score: float, confidence: float, evidence_count: int, baseline_mode: bool) -> TraceBand:
    if baseline_mode and evidence_count==0:
        return TraceBand.UNKNOWN
    if score>=75 and confidence>=0.5:
        return TraceBand.CRITICAL
    if score>=50:
        return TraceBand.HIGH
    if score>=25:
        return TraceBand.MEDIUM
    return TraceBand.LOW

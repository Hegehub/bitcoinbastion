from app.schemas.bastion_trace import ReviewPriority, ReviewStatus


def priority_from_band(trace_band: str) -> ReviewPriority:
    if trace_band in {"HIGH", "CRITICAL"}:
        return ReviewPriority.HIGH
    if trace_band == "MEDIUM":
        return ReviewPriority.MEDIUM
    return ReviewPriority.LOW


def is_open_status(status: ReviewStatus) -> bool:
    return status in {ReviewStatus.OPEN, ReviewStatus.IN_REVIEW, ReviewStatus.NEEDS_MORE_EVIDENCE}

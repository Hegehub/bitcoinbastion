from pydantic import BaseModel


class OperatorActionRequest(BaseModel):
    reviewer_id: int | None = None
    operator_note: str = ""
    decision_reason: str = ""
    confidence_override: float | None = None
    publish_override: bool = False


class OperatorReviewOut(BaseModel):
    id: int
    signal_candidate_id: int
    review_status: str
    reviewer_id: int | None
    operator_note: str
    decision_reason: str
    false_positive_marker: bool
    confidence_override: float | None
    publish_override: bool
    limitations: list[str]

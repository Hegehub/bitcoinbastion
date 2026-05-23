from app.schemas.bastion_trace import DestinationReviewLevel, DestinationReviewResult, SafeToSendAdvisory


def review(advisory: SafeToSendAdvisory | str) -> DestinationReviewResult:
    val = advisory.value if hasattr(advisory, "value") else str(advisory)
    level = DestinationReviewLevel.LIGHT_REVIEW
    reason = ["DESTINATION_REVIEW_LIGHT"]
    manual = False
    if val == SafeToSendAdvisory.MANUAL_REVIEW_RECOMMENDED.value:
        level = DestinationReviewLevel.MANUAL_REVIEW
        reason = ["DESTINATION_REVIEW_MANUAL"]
        manual = True
    if val == SafeToSendAdvisory.DO_NOT_PROCEED_WITHOUT_REVIEW.value:
        level = DestinationReviewLevel.SENIOR_REVIEW
        reason = ["DESTINATION_REVIEW_SENIOR"]
        manual = True
    return DestinationReviewResult(review_level=level, manual_review_recommended=manual, review_reasons=reason, operator_guidance=["Manual review is recommended before proceeding due to risk/context uncertainty."])

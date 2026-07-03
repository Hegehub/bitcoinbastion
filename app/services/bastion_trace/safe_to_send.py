from app.schemas.bastion_trace import AmountSensitivity, SafeToSendAdvisory


def decide(
    trace_band: str, confidence: float, amount_sensitivity: AmountSensitivity, disagreement: str
) -> SafeToSendAdvisory:
    if trace_band == "UNKNOWN" and amount_sensitivity == AmountSensitivity.UNKNOWN:
        return SafeToSendAdvisory.INSUFFICIENT_INFORMATION
    if trace_band in {"HIGH", "CRITICAL"}:
        return SafeToSendAdvisory.DO_NOT_PROCEED_WITHOUT_REVIEW
    if (
        disagreement in {"MEDIUM", "HIGH"}
        or confidence < 0.35
        or amount_sensitivity in {AmountSensitivity.HIGH, AmountSensitivity.VERY_HIGH}
    ):
        return SafeToSendAdvisory.MANUAL_REVIEW_RECOMMENDED
    return SafeToSendAdvisory.PROCEED_WITH_CAUTION

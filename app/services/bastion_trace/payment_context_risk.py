from datetime import UTC, datetime

from app.schemas.bastion_trace import PaymentContextRiskReport, PaymentDirection
from app.services.bastion_trace.context_sensitivity import ContextSensitivityService
from app.services.bastion_trace.destination_review import review
from app.services.bastion_trace.safe_to_send import decide


def evaluate_payment_context(
    address: str,
    trace_band: str,
    confidence: float,
    disagreement: str,
    amount_sats: int | None,
    direction: PaymentDirection,
    purpose: str | None,
    treasury: bool,
    urgent: bool,
    lens: dict[str, object],
) -> PaymentContextRiskReport:
    css = ContextSensitivityService()
    amount = css.amount_sensitivity(amount_sats)
    context = css.context_sensitivity(amount, treasury, urgent)
    advisory = decide(trace_band, confidence, amount, disagreement)
    dest = review(advisory)
    reasons = ["PAYMENT_CONTEXT_CREATED"]
    if amount_sats is None:
        reasons.append("PAYMENT_CONTEXT_AMOUNT_UNKNOWN")
    return PaymentContextRiskReport(
        payment_context_id=f"ctx-{address[:6]}-{int(datetime.now(UTC).timestamp())}",
        address=address,
        chain="bitcoin",
        amount_sats=amount_sats,
        direction=direction,
        context_risk_level=trace_band,
        context_sensitivity=context,
        amount_sensitivity=amount,
        counterparty_lens=lens,
        safe_to_send_advisory=advisory,
        manual_review_recommended=dest.manual_review_recommended,
        policy_hint="advisory_only",
        limitations=["payment_context_baseline_thresholds"],
        reason_codes=reasons,
        operator_guidance=["Bitcoin Bastion does not sign or send transactions in this workflow."],
        created_at=datetime.now(UTC),
    )

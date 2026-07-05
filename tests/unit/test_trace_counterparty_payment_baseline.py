from app.schemas.bastion_trace import AmountSensitivity, PaymentDirection
from app.services.bastion_trace.context_sensitivity import ContextSensitivityService
from app.services.bastion_trace.payment_context_risk import evaluate_payment_context


def test_amount_sensitivity_thresholds() -> None:
    svc = ContextSensitivityService()
    assert svc.amount_sensitivity(None) == AmountSensitivity.UNKNOWN
    assert svc.amount_sensitivity(99_999) == AmountSensitivity.LOW
    assert svc.amount_sensitivity(200_000) == AmountSensitivity.MEDIUM
    assert svc.amount_sensitivity(6_000_000) == AmountSensitivity.HIGH
    assert svc.amount_sensitivity(60_000_000) == AmountSensitivity.VERY_HIGH


def test_payment_context_address_only() -> None:
    report = evaluate_payment_context(
        "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
        "UNKNOWN",
        0.1,
        "NONE",
        None,
        PaymentDirection.UNKNOWN,
        None,
        False,
        False,
        {},
    )
    assert report.amount_sensitivity == AmountSensitivity.UNKNOWN
    assert report.safe_to_send_advisory.value == "INSUFFICIENT_INFORMATION"

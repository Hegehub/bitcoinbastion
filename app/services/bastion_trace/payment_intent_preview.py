from app.schemas.bastion_trace import PaymentContextRiskReport, PaymentIntentPreviewReport


def preview(report: PaymentContextRiskReport) -> PaymentIntentPreviewReport:
    data = report.model_dump(mode="python")
    data["transaction_signing_performed"] = False
    data["transaction_broadcast_performed"] = False
    return PaymentIntentPreviewReport(**data)

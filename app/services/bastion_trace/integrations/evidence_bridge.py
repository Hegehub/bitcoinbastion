from datetime import UTC, datetime


def build_refs(report_id: int) -> list[dict[str, object]]:
    now = datetime.now(UTC).isoformat()
    return [
        {
            "domain": "bastion_trace",
            "artifact_type": "TRACE_REPORT",
            "artifact_id": f"trace-report-{report_id}",
            "report_id": report_id,
            "created_at": now,
            "limitations": ["ref_only"],
        },
        {
            "domain": "bastion_trace",
            "artifact_type": "TRACE_RECEIPT",
            "artifact_id": f"trace-receipt-{report_id}",
            "report_id": report_id,
            "created_at": now,
            "limitations": ["baseline_receipt_placeholder"],
        },
    ]

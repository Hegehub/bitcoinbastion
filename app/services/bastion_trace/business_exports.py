from app.schemas.bastion_trace import BusinessExportFormat, BusinessExportResult


def create_business_export_payload(
    rows: list[dict[str, object]], fmt: BusinessExportFormat
) -> BusinessExportResult:
    if fmt == BusinessExportFormat.PDF_UNSUPPORTED:
        return BusinessExportResult(
            format=fmt,
            payload_text="PDF unsupported in baseline",
            limitations=["pdf_not_supported"],
            reason_codes=["ACCOUNTING_EXPORT_CREATED"],
        )
    if fmt == BusinessExportFormat.CSV:
        header = "address,trace_band,trace_score,confidence,policy_action,manual_review_recommended,report_id,created_at"
        lines = [header]
        for r in rows:
            lines.append(
                ",".join(
                    [
                        str(r.get("address", "")),
                        str(r.get("trace_band", "")),
                        str(r.get("trace_score", "")),
                        str(r.get("confidence", "")),
                        str(r.get("policy_action", "")),
                        str(r.get("manual_review_recommended", "")),
                        str(r.get("report_id", "")),
                        str(r.get("created_at", "")),
                    ]
                )
            )
        return BusinessExportResult(
            format=fmt,
            payload_text="\n".join(lines),
            reason_codes=["ACCOUNTING_EXPORT_CREATED"],
            limitations=[],
        )
    if fmt == BusinessExportFormat.MARKDOWN:
        body = "\n".join(
            [
                f"- {r.get('address')} | {r.get('trace_band')} | {r.get('policy_action')}"
                for r in rows
            ]
        )
        return BusinessExportResult(
            format=fmt,
            payload_text=f"# Business Trace Export\n\nAdvisory only.\n\n{body}",
            reason_codes=["ACCOUNTING_EXPORT_CREATED"],
            limitations=[],
        )
    return BusinessExportResult(
        format=fmt, payload_json=rows, reason_codes=["ACCOUNTING_EXPORT_CREATED"], limitations=[]
    )

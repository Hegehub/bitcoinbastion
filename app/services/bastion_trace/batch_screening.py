from app.schemas.bastion_trace import BatchTraceItemResult, BatchTraceResult, BusinessContextType


def make_batch_result(batch_id: int, label: str | None, context: BusinessContextType, items: list[BatchTraceItemResult], limitations: list[str]) -> BatchTraceResult:
    return BatchTraceResult(
        batch_id=batch_id,
        batch_label=label,
        business_context=context,
        total_addresses=len(items),
        processed_count=sum(1 for i in items if i.status == "processed"),
        rejected_count=sum(1 for i in items if i.status == "rejected"),
        low_count=sum(1 for i in items if i.trace_band == "LOW"),
        medium_count=sum(1 for i in items if i.trace_band == "MEDIUM"),
        high_count=sum(1 for i in items if i.trace_band == "HIGH"),
        critical_count=sum(1 for i in items if i.trace_band == "CRITICAL"),
        unknown_count=sum(1 for i in items if i.trace_band == "UNKNOWN"),
        manual_review_count=sum(1 for i in items if i.manual_review_recommended),
        reports=items,
        limitations=limitations,
    )

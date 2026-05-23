from app.schemas.bastion_trace import TraceConfidenceLedgerEntry, TraceFreshness, TraceSourceQuality


def compute_confidence(
    evidence_count: int,
    source_count: int,
    source_quality: TraceSourceQuality,
    freshness: TraceFreshness,
    provider_disagreement: float,
    node_backed: float,
    baseline_mode: bool,
) -> tuple[float, list[TraceConfidenceLedgerEntry]]:
    confidence = 0.2
    ledger: list[TraceConfidenceLedgerEntry] = []

    if evidence_count == 0:
        confidence -= 0.1
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="evidence_count",
                delta=-0.1,
                reason="No independent evidence sources were available.",
            )
        )
    elif evidence_count >= 2:
        confidence += 0.2
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="evidence_count",
                delta=0.2,
                reason="Multiple evidence items available.",
            )
        )

    if source_count >= 2:
        confidence += 0.2
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="independent_sources",
                delta=0.2,
                reason="Multiple independent sources available.",
            )
        )

    if source_quality == TraceSourceQuality.HIGH:
        confidence += 0.15
    elif source_quality == TraceSourceQuality.LOW:
        confidence -= 0.1

    if freshness == TraceFreshness.STALE:
        confidence -= 0.15
        ledger.append(TraceConfidenceLedgerEntry(factor="freshness", delta=-0.15, reason="Evidence is stale."))

    disagreement_delta = min(0.25, provider_disagreement * 0.25)
    confidence -= disagreement_delta
    if provider_disagreement > 0:
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="provider_disagreement",
                delta=-disagreement_delta,
                reason="Source disagreement lowers reliability.",
            )
        )

    if node_backed > 0:
        boost = min(0.1, node_backed * 0.1)
        confidence += boost
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="node_backed_confirmation",
                delta=boost,
                reason="Node-backed chain facts increase confidence.",
            )
        )

    if baseline_mode:
        confidence = min(confidence, 0.35)
        ledger.append(
            TraceConfidenceLedgerEntry(
                factor="baseline_mode",
                delta=-0.2,
                reason="Report is based on baseline deterministic logic only.",
            )
        )

    return max(0.0, min(1.0, confidence)), ledger

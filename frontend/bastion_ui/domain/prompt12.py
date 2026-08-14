"""Default-deny Feature-54 projections for Trace Submit and Report."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in value) if isinstance(value, list) else ()


@dataclass(frozen=True, slots=True)
class TraceSubmissionViewModel:
    report_id: str
    normalized_subject: str
    status: str
    idempotency_replayed: bool


@dataclass(frozen=True, slots=True)
class TraceReportViewModel:
    report_id: str
    subject: str
    chain: str
    status: str
    summary: str
    advisory_band: str
    score: float
    confidence: float
    source_quality: str
    freshness: str
    limitations: tuple[str, ...]
    evidence_references: tuple[str, ...]
    created_at: str


def adapt_trace_submission(payload: Any) -> TraceSubmissionViewModel:
    if not isinstance(payload, dict):
        raise ValueError("trace_submission_payload_invalid")
    return TraceSubmissionViewModel(
        report_id=str(payload["report_id"]),
        normalized_subject=str(payload["normalized_subject"]),
        status=str(payload["status"]),
        idempotency_replayed=bool(payload.get("idempotency_replayed", False)),
    )


def adapt_trace_report(payload: Any) -> TraceReportViewModel:
    if not isinstance(payload, dict):
        raise ValueError("trace_report_payload_invalid")
    return TraceReportViewModel(
        report_id=str(payload["id"]),
        subject=str(payload["address"]),
        chain=str(payload["chain"]),
        status=str(payload["status"]),
        summary=str(payload["summary"]),
        advisory_band=str(payload["trace_band"]),
        score=float(payload["trace_score"]),
        confidence=float(payload["confidence"]),
        source_quality=str(payload["source_quality"]),
        freshness=str(payload["freshness"]),
        limitations=_strings(payload.get("limitations")),
        evidence_references=_strings(payload.get("evidence_refs")),
        created_at=str(payload.get("created_at") or "Unavailable"),
    )

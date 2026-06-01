from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news_source import NewsSource
from app.db.models.provider_confidence_event import ProviderConfidenceEvent
from app.db.models.source_health_record import SourceHealthRecord
from app.db.models.source_health_snapshot import SourceHealthSnapshot


class SourceHealthBand:
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNSTABLE = "UNSTABLE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class SourceFailureType:
    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION"
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    INVALID_RSS = "INVALID_RSS"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    INVALID_CONTENT = "INVALID_CONTENT"
    RATE_LIMIT = "RATE_LIMIT"
    PARSING_ERROR = "PARSING_ERROR"
    DUPLICATE_SPAM = "DUPLICATE_SPAM"
    UNKNOWN = "UNKNOWN"


@dataclass
class HealthResult:
    success: bool
    status_code: int | None
    latency_ms: int | None
    failure_type: str | None = None
    error_message: str | None = None
    response_size_bytes: int | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_hash: str | None = None


class ProviderConfidenceService:
    def calculate_provider_confidence(self, source: NewsSource) -> float:
        value = source.provider_confidence
        if source.consecutive_failures >= 10:
            value -= 0.2
        elif source.consecutive_failures >= 3:
            value -= 0.05
        if source.avg_latency_ms and source.avg_latency_ms > 10000:
            value -= 0.08
        elif source.avg_latency_ms and source.avg_latency_ms > 3000:
            value -= 0.03
        if source.consecutive_successes >= 100:
            value += 0.06
        elif source.consecutive_successes >= 20:
            value += 0.02
        return max(0.05, min(0.99, round(value, 4)))

    def apply_health_result(self, db: Session, source: NewsSource, result: HealthResult) -> SourceHealthRecord:
        before = source.provider_confidence
        now = datetime.now(UTC)
        if result.success:
            source.success_count += 1
            source.consecutive_successes += 1
            source.consecutive_failures = 0
            source.last_success_at = now
            source.last_error = None
        else:
            source.failure_count += 1
            source.consecutive_failures += 1
            source.consecutive_successes = 0
            source.last_failure_at = now
            source.last_error = result.error_message
        source.last_status_code = result.status_code
        source.last_checked_at = now
        source.avg_latency_ms = self._next_latency(source.avg_latency_ms, result.latency_ms)
        source.provider_confidence = self.calculate_provider_confidence(source)
        source.health_band = self.calculate_health_band(source)
        source.is_degraded = source.provider_confidence < 0.4 or source.consecutive_failures >= 5
        source.backoff_until = self._next_backoff(source)
        rec = SourceHealthRecord(source_id=source.id, check_started_at=now, check_finished_at=now, status=source.health_band, status_code=result.status_code, success=result.success, failure_type=result.failure_type, latency_ms=result.latency_ms, response_size_bytes=result.response_size_bytes, etag=result.etag, last_modified=result.last_modified, content_hash=result.content_hash, provider_confidence_before=before, provider_confidence_after=source.provider_confidence, failure_count_snapshot=source.failure_count, success_count_snapshot=source.success_count, backoff_until=source.backoff_until, error_message=result.error_message, metadata_json={"is_degraded": source.is_degraded})
        db.add(rec)
        self.record_confidence_event(db, source.id, "health_result", before, source.provider_confidence, "health_apply", {"band": source.health_band})
        db.add(source)
        db.commit()
        db.refresh(rec)
        return rec

    def calculate_health_band(self, source: NewsSource) -> str:
        if source.consecutive_failures >= 10 or source.provider_confidence < 0.2:
            return SourceHealthBand.FAILED
        if source.consecutive_failures >= 5 or source.provider_confidence < 0.4:
            return SourceHealthBand.DEGRADED
        if source.avg_latency_ms and source.avg_latency_ms > 3000:
            return SourceHealthBand.UNSTABLE
        if source.success_count == 0 and source.failure_count == 0:
            return SourceHealthBand.UNKNOWN
        return SourceHealthBand.HEALTHY

    def build_health_snapshot(self, db: Session, source: NewsSource, window: str) -> SourceHealthSnapshot:
        records = list(db.execute(select(SourceHealthRecord).where(SourceHealthRecord.source_id == source.id).order_by(SourceHealthRecord.id.desc()).limit(200)).scalars())
        total = len(records)
        success = len([r for r in records if r.success])
        lats = sorted([r.latency_ms for r in records if r.latency_ms is not None])
        p95 = lats[int(len(lats)*0.95)-1] if lats else None
        snap = SourceHealthSnapshot(source_id=source.id, snapshot_window=window, success_rate=(success/total if total else 0.0), failure_rate=((total-success)/total if total else 0.0), avg_latency_ms=(sum(lats)/len(lats) if lats else None), median_latency_ms=(lats[len(lats)//2] if lats else None), p95_latency_ms=p95, provider_confidence=source.provider_confidence, consecutive_failures=source.consecutive_failures, consecutive_successes=source.consecutive_successes, last_success_at=source.last_success_at, last_failure_at=source.last_failure_at, degraded_state=source.is_degraded, health_band=source.health_band)
        db.add(snap)
        db.commit()
        db.refresh(snap)
        return snap

    def record_confidence_event(self, db: Session, source_id: int, event_type: str, old: float, new: float, reason: str, explanation: dict[str, object]) -> None:
        db.add(ProviderConfidenceEvent(source_id=source_id, event_type=event_type, old_confidence=old, new_confidence=new, delta=round(new-old, 4), reason_code=reason, explanation_json=explanation))

    def _next_latency(self, current: float | None, new: int | None) -> float | None:
        if new is None:
            return current
        return float(new) if current is None else (current * 0.8 + float(new) * 0.2)

    def _next_backoff(self, source: NewsSource) -> datetime | None:
        if source.consecutive_failures >= 10:
            return datetime.now(UTC).replace(microsecond=0)
        if source.consecutive_failures >= 3:
            return datetime.now(UTC).replace(microsecond=0)
        return None

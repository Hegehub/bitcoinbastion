from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.intelligence_signals import IntelligenceSignalDeliveryLog
from app.db.models.time_utils import utcnow
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.services.intelligence.signal_governance_metrics import (
    INTELLIGENCE_SIGNAL_DELIVERY_FAILURES_TOTAL,
    INTELLIGENCE_SIGNAL_PUBLISHED_TOTAL,
)

CHANNELS = {"telegram", "api", "web", "internal"}


class SignalDeliveryLogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IntelligenceSignalRepository(db)

    def record(
        self,
        signal_candidate_id: int,
        *,
        channel: str,
        delivery_status: str,
        target: str = "",
        message_id: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        delivered_at: datetime | None = None,
    ) -> IntelligenceSignalDeliveryLog:
        bounded_channel = channel if channel in CHANNELS else "internal"
        row = IntelligenceSignalDeliveryLog(
            signal_candidate_id=signal_candidate_id,
            channel=bounded_channel,
            delivery_status=delivery_status,
            target=self._sanitize_target(target),
            message_id=message_id,
            error_type=self._sanitize_error_type(error_type),
            error_message_sanitized=self._sanitize_message(error_message),
            delivered_at=delivered_at if delivery_status == "success" else None,
        )
        if delivery_status == "success":
            row.delivered_at = row.delivered_at or utcnow()
            candidate = self.repo.get_candidate(signal_candidate_id)
            if candidate is not None:
                candidate.status = "published"
                candidate.published_at = candidate.published_at or row.delivered_at
                INTELLIGENCE_SIGNAL_PUBLISHED_TOTAL.labels(signal_type=self._bounded_type(candidate.signal_type), channel=bounded_channel).inc()
        else:
            INTELLIGENCE_SIGNAL_DELIVERY_FAILURES_TOTAL.labels(channel=bounded_channel, reason_code=self._sanitize_error_type(error_type) or "unknown").inc()
        self.repo.add_delivery_log(row)
        return row

    def payload(self, row: IntelligenceSignalDeliveryLog) -> dict[str, object]:
        return {
            "id": row.id,
            "signal_candidate_id": row.signal_candidate_id,
            "channel": row.channel,
            "delivery_status": row.delivery_status,
            "target": row.target,
            "message_id": row.message_id,
            "error_type": row.error_type,
            "error_message_sanitized": row.error_message_sanitized,
            "delivered_at": row.delivered_at,
            "created_at": row.created_at,
        }

    def _sanitize_target(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_@.:-]", "_", value or "")[:160]

    def _sanitize_error_type(self, value: str | None) -> str | None:
        if value is None:
            return None
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", value.lower())[:80]
        return sanitized or "unknown"

    def _sanitize_message(self, value: str | None) -> str | None:
        if value is None:
            return None
        return re.sub(r"(token|secret|key|password)=\S+", r"\1=[redacted]", value, flags=re.IGNORECASE)[:500]

    def _bounded_type(self, value: str) -> str:
        return value if value in {"news_market_impact", "candle_attribution", "delayed_reaction", "false_signal", "security_shock", "regulatory_risk", "macro_shock", "narrative_spike", "news_shock_index"} else "other"

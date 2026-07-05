from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.intelligence_signals import IntelligenceSignalCandidate
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.schemas.intelligence_signals import SIGNAL_LIMITATIONS

PROHIBITED_TERMS = ["guaranteed", "will pump", "will dump", "caused by", "certain"]


class SignalGovernanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IntelligenceSignalRepository(db)

    def public_payload(self, candidate: IntelligenceSignalCandidate) -> dict[str, Any]:
        reviews = self.repo.reviews_for(candidate.id)
        evidence_refs = self.evidence_refs(candidate)
        evidence_count = self._evidence_count(evidence_refs)
        operator_status = (
            reviews[0].review_status
            if reviews
            else "pending" if candidate.requires_operator_review else "policy_only"
        )
        payload = {
            "signal_id": candidate.id,
            "signal_type": candidate.signal_type,
            "title": self._safe_text(candidate.title),
            "summary": self._safe_text(candidate.summary),
            "confidence_score": candidate.confidence_score,
            "evidence_refs": evidence_refs,
            "limitations": SIGNAL_LIMITATIONS.copy(),
            "correlation_not_causation": True,
            "not_financial_advice": True,
            "operator_reviewed": bool(reviews),
            "evidence_based": evidence_count > 0,
            "published_at": candidate.published_at,
            "status": candidate.status,
            "display_title": self._safe_text(candidate.title),
            "display_summary": self._safe_text(candidate.summary),
            "badge_label": self._badge_label(candidate),
            "badge_severity": self._badge_severity(candidate),
            "confidence_percent": int(round(max(0.0, min(1.0, candidate.confidence_score)) * 100)),
            "top_reasons": self._top_reasons(candidate),
            "evidence_count": evidence_count,
            "limitations_count": len(SIGNAL_LIMITATIONS),
            "operator_status": operator_status,
            "can_approve": candidate.status in {"pending_review", "held", "degraded"},
            "can_reject": candidate.status in {"pending_review", "held", "approved", "degraded"},
            "can_hold": candidate.status in {"pending_review", "approved"},
            "can_mark_false_positive": candidate.status != "published",
        }
        return payload

    def evidence_refs(self, candidate: IntelligenceSignalCandidate) -> dict[str, object]:
        refs: dict[str, object] = {}
        for key in [
            "article_id",
            "event_id",
            "candle_id",
            "impact_id",
            "attribution_id",
            "evidence_packet_id",
        ]:
            value = getattr(candidate, key)
            if value is not None:
                refs[key] = value
        if candidate.attribution_id is not None:
            refs["replay_evidence"] = f"candle_attribution_replay:{candidate.attribution_id}"
        if candidate.event_id is not None or candidate.article_id is not None:
            refs["source_health_snapshot"] = "source_health_latest_available"
        if candidate.provider_confidence is not None:
            refs["provider_confidence_snapshot"] = {
                "provider_confidence": candidate.provider_confidence,
                "degraded": candidate.provider_confidence < 0.6,
            }
        refs["limitations"] = SIGNAL_LIMITATIONS.copy()
        return refs

    def list_public(
        self, *, status: str | None = None, signal_type: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        rows = self.repo.list_candidates(status=status, signal_type=signal_type, limit=limit)
        return [self.public_payload(row) for row in rows]

    def get_public(self, signal_id: int) -> dict[str, Any] | None:
        row = self.repo.get_candidate(signal_id)
        return self.public_payload(row) if row else None

    def _evidence_count(self, refs: dict[str, object]) -> int:
        primary_keys = {
            "article_id",
            "event_id",
            "candle_id",
            "impact_id",
            "attribution_id",
            "evidence_packet_id",
            "replay_evidence",
            "source_health_snapshot",
        }
        return len([key for key in refs if key in primary_keys])

    def _top_reasons(self, candidate: IntelligenceSignalCandidate) -> list[str]:
        reasons = [item for item in candidate.policy_reason.split(",") if item]
        return reasons[:3] or ["evidence_based_candidate"]

    def _badge_label(self, candidate: IntelligenceSignalCandidate) -> str:
        if candidate.status == "published":
            return "Published"
        if candidate.requires_operator_review:
            return "Review required"
        return "Policy cleared"

    def _badge_severity(self, candidate: IntelligenceSignalCandidate) -> str:
        if candidate.signal_type in {"security_shock", "regulatory_risk", "false_signal"}:
            return "high"
        if candidate.confidence_score >= 0.75:
            return "medium"
        return "low"

    def _safe_text(self, value: str) -> str:
        output = value or ""
        for term in PROHIBITED_TERMS:
            output = re.sub(re.escape(term), "prohibited claim", output, flags=re.IGNORECASE)
        return output

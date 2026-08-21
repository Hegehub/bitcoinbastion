from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.bastion_trace.claims.persistence import TraceClaimRepository
from app.services.bastion_trace.claims.domain import TraceClaim
from app.services.bastion_trace.disagreement.domain import TraceDisagreementEvaluation
from app.services.bastion_trace.disagreement.evaluator import TraceDisagreementEvaluator


class TraceHistoricalDisagreementService:
    """Derives D2 results only from Claims immutably captured for one report."""

    def __init__(self, db: Session) -> None:
        self._claims = TraceClaimRepository(db)
        self._evaluator = TraceDisagreementEvaluator()

    def for_report(self, report_id: int) -> tuple[TraceDisagreementEvaluation, ...]:
        claims = self._claims.load_claims_for_report(report_id)
        groups: dict[tuple[str, str], list[TraceClaim]] = {}
        for claim in claims:
            groups.setdefault((claim.subject.object_id, claim.predicate.value), []).append(claim)
        return tuple(
            self._evaluator.evaluate(tuple(groups[key]))
            for key in sorted(groups)
        )

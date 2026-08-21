from __future__ import annotations

import json

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.models.bastion_trace import TraceClaimModel
from app.services.bastion_trace.claims.domain import RiskBandClaimValue, TraceClaim
from app.schemas.bastion_trace import TraceBand
from app.services.bastion_trace.claims.domain import (
    BitcoinNetworkClaimValue,
    TraceClaimPredicate,
    TraceClaimProvenance,
    TraceClaimSubject,
    TraceClaimSubjectKind,
    TraceClaimValueKind,
)


class TraceClaimRepository:
    """Append-only persistence for claims captured with a Trace report."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add_claims(self, report_id: int, claims: tuple[TraceClaim, ...]) -> None:
        if not claims or not self.is_available():
            return
        existing = set(
            self._db.execute(
                select(TraceClaimModel.id).where(
                    TraceClaimModel.id.in_(claim.id for claim in claims)
                )
            ).scalars()
        )
        for claim in claims:
            if claim.id in existing:
                continue
            value_text = (
                claim.value.band.value
                if isinstance(claim.value, RiskBandClaimValue)
                else claim.value.network
            )
            self._db.add(
                TraceClaimModel(
                    id=claim.id,
                    report_id=report_id,
                    capture_id=claim.capture_id,
                    claim_schema_version=claim.claim_schema_version,
                    subject_kind=claim.subject.kind.value,
                    subject_id=claim.subject.object_id,
                    subject_public_value=claim.subject.public_value,
                    predicate=claim.predicate.value,
                    value_kind=claim.value.kind.value,
                    value_text=value_text,
                    producer_id=claim.producer_id,
                    producer_version=claim.producer_version,
                    source_id=claim.source_id,
                    evaluated_at=claim.evaluated_at,
                    confidence=claim.confidence,
                    input_references_json=json.dumps(claim.provenance.input_references),
                    limitations_json=json.dumps(claim.limitations),
                )
            )
        self._db.commit()

    def list_for_report(self, report_id: int) -> tuple[TraceClaimModel, ...]:
        if not self.is_available():
            return ()
        rows = self._db.execute(
            select(TraceClaimModel)
            .where(TraceClaimModel.report_id == report_id)
            .order_by(TraceClaimModel.id)
        ).scalars()
        return tuple(rows)

    def is_available(self) -> bool:
        bind = self._db.get_bind()
        return bool(inspect(bind).has_table(TraceClaimModel.__tablename__))

    def load_claims_for_report(self, report_id: int) -> tuple[TraceClaim, ...]:
        return tuple(self._to_domain(row) for row in self.list_for_report(report_id))

    def _to_domain(self, row: TraceClaimModel) -> TraceClaim:
        value_kind = TraceClaimValueKind(row.value_kind)
        value = (
            RiskBandClaimValue(value_kind, TraceBand(row.value_text))
            if value_kind is TraceClaimValueKind.RISK_BAND
            else BitcoinNetworkClaimValue(value_kind, row.value_text)
        )
        input_references = tuple(str(item) for item in json.loads(row.input_references_json))
        limitations = tuple(str(item) for item in json.loads(row.limitations_json))
        return TraceClaim(
            id=row.id,
            claim_schema_version=row.claim_schema_version,
            capture_id=row.capture_id,
            subject=TraceClaimSubject(
                TraceClaimSubjectKind(row.subject_kind),
                row.subject_id,
                row.subject_public_value,
            ),
            predicate=TraceClaimPredicate(row.predicate),
            value=value,
            producer_id=row.producer_id,
            producer_version=row.producer_version,
            source_id=row.source_id,
            evaluated_at=row.evaluated_at,
            provenance=TraceClaimProvenance(input_references, limitations),
            confidence=row.confidence,
            limitations=limitations,
        )

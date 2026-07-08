import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.bastion_trace import (
    TraceBatch,
    TraceBatchItem,
    TraceBusinessEventModel,
    TraceBusinessExportModel,
    TraceBusinessPolicyProfileModel,
    TraceBusinessProofPacketModel,
    TraceEvidence,
    TraceOperatorNoteModel,
    TraceReport,
    TraceReviewItem,
    TraceSource,
    TraceWatchlistEntry,
)


class BastionTraceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_report(self, report: TraceReport) -> TraceReport:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: int) -> TraceReport | None:
        return self.db.execute(
            select(TraceReport).where(TraceReport.id == report_id)
        ).scalar_one_or_none()

    def list_evidence(self, report_id: int) -> list[TraceEvidence]:
        return list(
            self.db.execute(
                select(TraceEvidence).where(TraceEvidence.report_id == report_id)
            ).scalars()
        )

    def list_sources(self) -> list[TraceSource]:
        return list(self.db.execute(select(TraceSource).order_by(TraceSource.id.desc())).scalars())

    def list_watchlist_entries(self) -> list[TraceWatchlistEntry]:
        return list(
            self.db.execute(
                select(TraceWatchlistEntry).where(TraceWatchlistEntry.active.is_(True))
            ).scalars()
        )

    def add_watchlist_entry(
        self, address: str, label: str, reason: str, risk_hint: str
    ) -> TraceWatchlistEntry:
        entry = TraceWatchlistEntry(
            address=address, label=label, reason=reason, risk_hint=risk_hint
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def create_source(
        self,
        source_name: str,
        source_type: str,
        trust_level: str,
        enabled: bool,
        limitations: list[str],
    ) -> TraceSource:
        item = TraceSource(
            source_name=source_name,
            source_type=source_type,
            trust_level=trust_level,
            enabled=enabled,
            limitations_json=json.dumps(limitations),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save_origin_metadata(
        self,
        report_id: int,
        origin_passport: dict[str, object],
        provider_disagreement: dict[str, object],
        evidence_independence: dict[str, object],
        source_status_summary: list[dict[str, object]],
    ) -> None:
        report = self.get_report(report_id)
        if report is None:
            return
        report.origin_passport_json = json.dumps(origin_passport)
        report.provider_disagreement_json = json.dumps(provider_disagreement)
        report.evidence_independence_json = json.dumps(evidence_independence)
        report.source_status_summary_json = json.dumps(source_status_summary)
        self.db.add(report)
        self.db.commit()

    def save_privacy_metadata(self, report_id: int, payload: dict[str, object]) -> None:
        report = self.get_report(report_id)
        if report is None:
            return
        report.privacy_shield_json = json.dumps(payload)
        report.utxo_hygiene_json = json.dumps(payload.get("utxo_hygiene", {}))
        report.dust_radar_json = json.dumps(payload.get("dust_radar", {}))
        report.address_reuse_json = json.dumps(payload.get("address_reuse", {}))
        report.consolidation_risk_json = json.dumps(payload.get("consolidation_risk", {}))
        report.toxic_change_json = json.dumps(payload.get("toxic_change", {}))
        self.db.add(report)
        self.db.commit()

    def save_counterparty_lens(self, report_id: int, payload: dict[str, object]) -> None:
        report = self.get_report(report_id)
        if report is None:
            return
        report.counterparty_lens_json = json.dumps(payload)
        self.db.add(report)
        self.db.commit()

    def create_batch(self, batch: TraceBatch) -> TraceBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_batch(self, batch_id: int) -> TraceBatch | None:
        return self.db.execute(
            select(TraceBatch).where(TraceBatch.id == batch_id)
        ).scalar_one_or_none()

    def add_batch_item(self, item: TraceBatchItem) -> TraceBatchItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_batch_items(self, batch_id: int) -> list[TraceBatchItem]:
        return list(
            self.db.execute(
                select(TraceBatchItem).where(TraceBatchItem.batch_id == batch_id)
            ).scalars()
        )

    def list_policy_profiles(self) -> list[TraceBusinessPolicyProfileModel]:
        return list(
            self.db.execute(
                select(TraceBusinessPolicyProfileModel).order_by(
                    TraceBusinessPolicyProfileModel.name.asc()
                )
            ).scalars()
        )

    def get_policy_profile(self, profile_id: str) -> TraceBusinessPolicyProfileModel | None:
        return self.db.execute(
            select(TraceBusinessPolicyProfileModel).where(
                TraceBusinessPolicyProfileModel.id == profile_id
            )
        ).scalar_one_or_none()

    def save_policy_profile(
        self, item: TraceBusinessPolicyProfileModel
    ) -> TraceBusinessPolicyProfileModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def create_review_item(self, item: TraceReviewItem) -> TraceReviewItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_review_items(self) -> list[TraceReviewItem]:
        return list(
            self.db.execute(select(TraceReviewItem).order_by(TraceReviewItem.id.desc())).scalars()
        )

    def get_review_item(self, review_item_id: int) -> TraceReviewItem | None:
        return self.db.execute(
            select(TraceReviewItem).where(TraceReviewItem.id == review_item_id)
        ).scalar_one_or_none()

    def save_operator_note(self, item: TraceOperatorNoteModel) -> TraceOperatorNoteModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_operator_notes(self, review_item_id: int) -> list[TraceOperatorNoteModel]:
        return list(
            self.db.execute(
                select(TraceOperatorNoteModel).where(
                    TraceOperatorNoteModel.review_item_id == review_item_id
                )
            ).scalars()
        )

    def save_business_proof_packet(
        self, item: TraceBusinessProofPacketModel
    ) -> TraceBusinessProofPacketModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save_business_export(self, item: TraceBusinessExportModel) -> TraceBusinessExportModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save_business_event(self, item: TraceBusinessEventModel) -> TraceBusinessEventModel:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_business_events(self) -> list[TraceBusinessEventModel]:
        return list(
            self.db.execute(
                select(TraceBusinessEventModel).order_by(TraceBusinessEventModel.id.desc())
            ).scalars()
        )

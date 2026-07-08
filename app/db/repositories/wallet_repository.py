import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.wallet import WalletHealthReport, WalletProfile
from app.schemas.wallet import WalletHealthResponse
from app.services.events.domain_event_publisher import publish_domain_event


class WalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_profile(self, wallet_profile_id: int) -> WalletProfile | None:
        stmt = select(WalletProfile).where(WalletProfile.id == wallet_profile_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: int, limit: int, offset: int) -> list[WalletProfile]:
        stmt = (
            select(WalletProfile)
            .where(WalletProfile.user_id == user_id)
            .order_by(WalletProfile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def count_by_user(self, user_id: int) -> int:
        stmt = (
            select(func.count()).select_from(WalletProfile).where(WalletProfile.user_id == user_id)
        )
        return int(self.db.execute(stmt).scalar_one())

    def create_health_report(
        self, wallet_profile_id: int, health: WalletHealthResponse
    ) -> WalletHealthReport:
        report = WalletHealthReport(
            wallet_profile_id=wallet_profile_id,
            health_score=health.health_score,
            utxo_fragmentation_score=health.utxo_fragmentation_score,
            privacy_score=health.privacy_score,
            fee_exposure_score=health.fee_exposure_score,
            recommendations_json=json.dumps(health.recommendations),
            findings_json=json.dumps(
                {
                    "health_score": health.health_score,
                    "utxo_fragmentation_score": health.utxo_fragmentation_score,
                    "privacy_score": health.privacy_score,
                    "fee_exposure_score": health.fee_exposure_score,
                }
            ),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        publish_domain_event(
            self.db,
            "wallet.health.generated",
            {
                "wallet_id": wallet_profile_id,
                "health_status": "generated",
                "privacy_risk_band": "high" if health.privacy_score < 0.4 else "baseline",
                "risk_reasons": health.recommendations,
                "confidence": health.confidence,
                "limitations": [
                    "Wallet health events contain derived health metadata only.",
                    "No custody or secret wallet material is accepted.",
                ],
                "no_custody": True,
            },
            aggregate_type="wallet_health",
            aggregate_id=report.id,
            source="wallet_health_service",
            idempotency_key=f"wallet.health.generated:wallet_health:{report.id}:generated",
        )
        if health.privacy_score < 0.4:
            publish_domain_event(
                self.db,
                "wallet.privacy_risk.high",
                {
                    "wallet_id": wallet_profile_id,
                    "health_status": "generated",
                    "privacy_risk_band": "high",
                    "risk_reasons": health.recommendations,
                    "confidence": health.confidence,
                    "limitations": ["Wallet privacy risk is advisory-only and no-custody."],
                    "no_custody": True,
                    "advisory_only": True,
                },
                aggregate_type="wallet_health",
                aggregate_id=report.id,
                source="wallet_health_service",
                idempotency_key=f"wallet.privacy_risk.high:wallet_health:{report.id}:high",
            )
        return report

    def list_health_reports(
        self, wallet_profile_id: int, limit: int, offset: int
    ) -> list[WalletHealthReport]:
        stmt = (
            select(WalletHealthReport)
            .where(WalletHealthReport.wallet_profile_id == wallet_profile_id)
            .order_by(WalletHealthReport.generated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def count_health_reports(self, wallet_profile_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(WalletHealthReport)
            .where(WalletHealthReport.wallet_profile_id == wallet_profile_id)
        )
        return int(self.db.execute(stmt).scalar_one())

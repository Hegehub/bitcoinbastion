from app.schemas.bastion_trace import (
    ProviderDisagreementResult,
    ProviderDisagreementSeverity,
    ProviderDisagreementType,
)


class ProviderDisagreementService:
    def detect_disagreement(
        self, origin_labels: list[str], risk_bands: list[str]
    ) -> ProviderDisagreementResult:
        if len(origin_labels) <= 1 and len(risk_bands) <= 1:
            return ProviderDisagreementResult(
                has_disagreement=False,
                severity=ProviderDisagreementSeverity.NONE,
                disagreement_type=ProviderDisagreementType.NO_CONFLICT,
                description="No conflicting providers",
                affected_fields=[],
                source_names=[],
                confidence_impact=0.0,
                manual_review_recommended=False,
                reason_codes=[],
            )
        if len(set(risk_bands)) > 1:
            return ProviderDisagreementResult(
                has_disagreement=True,
                severity=ProviderDisagreementSeverity.MEDIUM,
                disagreement_type=ProviderDisagreementType.RISK_BAND_CONFLICT,
                description="Risk bands conflict across sources",
                affected_fields=["risk_band"],
                source_names=[],
                confidence_impact=0.15,
                manual_review_recommended=True,
                reason_codes=[
                    "PROVIDER_DISAGREEMENT_MEDIUM",
                    "MANUAL_REVIEW_DUE_TO_SOURCE_CONFLICT",
                ],
            )
        if len(set(origin_labels)) > 1:
            return ProviderDisagreementResult(
                has_disagreement=True,
                severity=ProviderDisagreementSeverity.MEDIUM,
                disagreement_type=ProviderDisagreementType.ORIGIN_CONFLICT,
                description="Origin categories conflict across sources",
                affected_fields=["origin_category"],
                source_names=[],
                confidence_impact=0.1,
                manual_review_recommended=True,
                reason_codes=[
                    "PROVIDER_DISAGREEMENT_MEDIUM",
                    "MANUAL_REVIEW_DUE_TO_SOURCE_CONFLICT",
                ],
            )
        return ProviderDisagreementResult(
            has_disagreement=False,
            severity=ProviderDisagreementSeverity.NONE,
            disagreement_type=ProviderDisagreementType.NO_CONFLICT,
            description="No conflicting providers",
            affected_fields=[],
            source_names=[],
            confidence_impact=0.0,
            manual_review_recommended=False,
            reason_codes=[],
        )

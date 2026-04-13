from app.schemas.privacy import PrivacyAssessmentRequest, PrivacyAssessmentResponse


class PrivacyRiskService:
    def assess(self, payload: PrivacyAssessmentRequest) -> PrivacyAssessmentResponse:
        risk_score = min(
            100.0,
            payload.reused_addresses * 5.0
            + (30.0 if payload.known_kyc_exposure else 0.0)
            + payload.utxo_fragmentation_score * 35.0,
        )
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 35:
            risk_level = "medium"
        else:
            risk_level = "low"

        recommendations = [
            "Avoid address reuse and generate a fresh receive address for each payment.",
            "Use coin control to avoid merging UTXOs with unrelated histories.",
        ]
        if payload.known_kyc_exposure:
            recommendations.append("Segregate KYC and non-KYC funds into separate wallets.")

        return PrivacyAssessmentResponse(
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            recommendations=recommendations,
        )

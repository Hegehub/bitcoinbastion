from app.schemas.privacy import PrivacyAssessmentRequest, PrivacyAssessmentResponse


class PrivacyRiskService:
    def assess(self, payload: PrivacyAssessmentRequest) -> PrivacyAssessmentResponse:
        reuse_component = min(35.0, payload.reused_addresses * 5.0)
        kyc_component = 30.0 if payload.known_kyc_exposure else 0.0
        fragmentation_component = payload.utxo_fragmentation_score * 20.0
        cluster_component = min(15.0, payload.merged_clusters_count * 3.0)

        risk_score = min(100.0, reuse_component + kyc_component + fragmentation_component + cluster_component)
        if risk_score >= 70:
            risk_level = "high"
            priority_action = "Stop consolidation and isolate high-risk UTXOs before next spend."
        elif risk_score >= 35:
            risk_level = "medium"
            priority_action = "Apply strict coin control before the next transaction."
        else:
            risk_level = "low"
            priority_action = "Maintain current hygiene and continue avoiding address reuse."

        recommendations = [
            "Avoid address reuse and generate a fresh receive address for each payment.",
            "Use coin control to avoid merging UTXOs with unrelated histories.",
        ]
        if payload.known_kyc_exposure:
            recommendations.append("Segregate KYC and non-KYC funds into separate wallets.")
        if payload.merged_clusters_count > 0:
            recommendations.append("Spend from one privacy cluster at a time to reduce linkage amplification.")

        explainability: dict[str, float | str] = {
            "reuse_component": round(reuse_component, 2),
            "kyc_component": round(kyc_component, 2),
            "fragmentation_component": round(fragmentation_component, 2),
            "cluster_component": round(cluster_component, 2),
            "model": "privacy_risk_v1",
        }

        return PrivacyAssessmentResponse(
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            recommendations=recommendations,
            priority_action=priority_action,
            explainability=explainability,
        )

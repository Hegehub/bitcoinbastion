from app.schemas.bastion_trace import PrivacyRiskLevel, ToxicChangeReport


class ToxicChangeService:
    def build(self, has_graph_evidence: bool = False) -> ToxicChangeReport:
        if not has_graph_evidence:
            return ToxicChangeReport(
                toxic_change_risk_level=PrivacyRiskLevel.UNKNOWN,
                possible_toxic_change_detected=False,
                heuristic_confidence=0.2,
                limitations=["transaction_graph_unavailable"],
                reason_codes=["TOXIC_CHANGE_UNKNOWN"],
            )
        return ToxicChangeReport(
            toxic_change_risk_level=PrivacyRiskLevel.MEDIUM,
            possible_toxic_change_detected=True,
            heuristic_confidence=0.4,
            limitations=["heuristic_baseline"],
            reason_codes=["TOXIC_CHANGE_POSSIBLE"],
        )

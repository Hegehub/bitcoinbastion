from app.schemas.bastion_trace import EvidenceIndependenceResult


class EvidenceIndependenceService:
    def calculate(self, source_names: list[str]) -> EvidenceIndependenceResult:
        count = len(source_names)
        if count == 0:
            return EvidenceIndependenceResult(score=0.0, source_count=0, independent_source_count=0, dominant_source="", dominant_source_share=1.0, limitations=["source_limited"], reason_codes=["EVIDENCE_INDEPENDENCE_LOW"])
        uniq = len(set(source_names))
        dominant = max(set(source_names), key=source_names.count)
        dom_share = source_names.count(dominant) / count
        score = min(1.0, uniq / max(count, 1))
        if count == 1:
            score = min(score, 0.25)
        if dom_share > 0.8:
            score = min(score, 0.5)
        code = "EVIDENCE_INDEPENDENCE_LOW" if score < 0.35 else "EVIDENCE_INDEPENDENCE_MEDIUM" if score < 0.75 else "EVIDENCE_INDEPENDENCE_HIGH"
        return EvidenceIndependenceResult(score=score, source_count=count, independent_source_count=uniq, dominant_source=dominant, dominant_source_share=dom_share, limitations=[], reason_codes=[code])

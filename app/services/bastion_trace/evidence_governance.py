from app.schemas.bastion_trace import EvidenceAccessDecision


def decide_evidence_access(requester_role: str) -> EvidenceAccessDecision:
    if requester_role in {"OWNER", "ADMIN", "AUDITOR"}:
        return EvidenceAccessDecision.ALLOW
    if requester_role == "READ_ONLY":
        return EvidenceAccessDecision.REDACT
    return EvidenceAccessDecision.REQUIRE_APPROVAL

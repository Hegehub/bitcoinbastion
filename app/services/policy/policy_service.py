from app.schemas.policy import PolicyCheckRequest, PolicyCheckResponse


class TreasuryPolicyService:
    def evaluate(self, payload: PolicyCheckRequest) -> PolicyCheckResponse:
        violations: list[str] = []
        if payload.wallet_health_score < 60:
            violations.append("Wallet health is below minimum threshold (60).")
        if payload.transaction_amount_sats > 10_000_000:
            violations.append("Transaction exceeds single-approval policy limit.")

        allowed = not violations
        next_actions = (
            ["Proceed with PSBT creation and designated signer quorum workflow."]
            if allowed
            else [
                "Escalate to treasury operator review.",
                "Record justification in policy execution log.",
            ]
        )
        return PolicyCheckResponse(allowed=allowed, violations=violations, next_actions=next_actions)

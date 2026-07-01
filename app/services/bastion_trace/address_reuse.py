from app.schemas.bastion_trace import AddressReuseReport, PrivacyRiskLevel


class AddressReuseService:
    def build(self, reuse_count: int | None) -> AddressReuseReport:
        if reuse_count is None:
            return AddressReuseReport(
                reuse_detected=False,
                reuse_count=0,
                reuse_risk_level=PrivacyRiskLevel.UNKNOWN,
                limitations=["source_limited"],
                reason_codes=["ADDRESS_REUSE_UNKNOWN"],
            )
        detected = reuse_count > 1
        level = (
            PrivacyRiskLevel.HIGH
            if reuse_count > 10
            else PrivacyRiskLevel.MEDIUM if reuse_count > 3 else PrivacyRiskLevel.LOW
        )
        return AddressReuseReport(
            reuse_detected=detected,
            reuse_count=reuse_count,
            reuse_risk_level=level,
            limitations=[],
            reason_codes=["ADDRESS_REUSE_DETECTED" if detected else "ADDRESS_REUSE_UNKNOWN"],
        )

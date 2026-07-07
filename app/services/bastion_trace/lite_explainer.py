from app.schemas.bastion_trace import (
    LiteConfidenceLabel,
    LiteRiskLabel,
    LiteTraceStatus,
    PrivacyBand,
    TraceBand,
)


def map_risk_label(band: TraceBand) -> LiteRiskLabel:
    return {
        TraceBand.LOW: LiteRiskLabel.NO_STRONG_RISK_SIGNAL_FOUND,
        TraceBand.MEDIUM: LiteRiskLabel.CAUTION,
        TraceBand.HIGH: LiteRiskLabel.HIGH_CAUTION,
        TraceBand.CRITICAL: LiteRiskLabel.CRITICAL_REVIEW_REQUIRED,
        TraceBand.UNKNOWN: LiteRiskLabel.UNKNOWN,
    }[band]


def map_status(band: TraceBand) -> LiteTraceStatus:
    return {
        TraceBand.LOW: LiteTraceStatus.READY,
        TraceBand.MEDIUM: LiteTraceStatus.NEEDS_CAUTION,
        TraceBand.HIGH: LiteTraceStatus.MANUAL_REVIEW_RECOMMENDED,
        TraceBand.CRITICAL: LiteTraceStatus.MANUAL_REVIEW_RECOMMENDED,
        TraceBand.UNKNOWN: LiteTraceStatus.INSUFFICIENT_INFORMATION,
    }[band]


def map_privacy_label(band: str) -> str:
    b = PrivacyBand(band) if band in PrivacyBand._value2member_map_ else PrivacyBand.UNKNOWN
    return {
        PrivacyBand.LOW: "Low privacy exposure",
        PrivacyBand.MEDIUM: "Some privacy exposure",
        PrivacyBand.HIGH: "High privacy exposure",
        PrivacyBand.CRITICAL: "High privacy exposure",
        PrivacyBand.UNKNOWN: "Unknown privacy exposure",
    }[b]


def map_confidence_label(confidence: float) -> LiteConfidenceLabel:
    if confidence < 0.35:
        return LiteConfidenceLabel.LOW_CONFIDENCE
    if confidence < 0.7:
        return LiteConfidenceLabel.MEDIUM_CONFIDENCE
    return LiteConfidenceLabel.HIGH_CONFIDENCE

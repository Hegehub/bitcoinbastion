from app.schemas.bastion_trace import TraceBand, TraceScoringInput
from app.services.bastion_trace.scoring import score_trace


def test_empty_evidence_unknown() -> None:
    r = score_trace(TraceScoringInput(evidence_count=0, independent_source_count=0, baseline_mode=True))
    assert r.band == TraceBand.UNKNOWN


def test_baseline_cannot_high_or_critical() -> None:
    r = score_trace(TraceScoringInput(evidence_count=0, independent_source_count=0, baseline_mode=True, factors={"known_high_risk_exposure": 1.0}))
    assert r.band in {TraceBand.UNKNOWN, TraceBand.LOW}


def test_threshold_mapping() -> None:
    low = score_trace(TraceScoringInput(evidence_count=2, independent_source_count=2, baseline_mode=False, factors={"suspicious_pattern_signal": 0.5}))
    med = score_trace(TraceScoringInput(evidence_count=2, independent_source_count=2, baseline_mode=False, factors={"known_high_risk_exposure": 1.0}))
    high = score_trace(TraceScoringInput(evidence_count=2, independent_source_count=2, baseline_mode=False, factors={"known_high_risk_exposure": 1.0, "suspicious_pattern_signal": 1.0}))
    crit = score_trace(TraceScoringInput(evidence_count=3, independent_source_count=3, baseline_mode=False, factors={"known_high_risk_exposure": 1.0, "suspicious_pattern_signal": 1.0, "origin_uncertainty": 1.0, "privacy_leak_signal": 1.0}))
    assert low.band == TraceBand.LOW
    assert med.band == TraceBand.MEDIUM
    assert high.band == TraceBand.HIGH
    assert crit.band == TraceBand.CRITICAL


def test_dna_normalized() -> None:
    r = score_trace(TraceScoringInput(evidence_count=1, independent_source_count=1, baseline_mode=False, factors={"privacy_leak_signal": 1.0}))
    for v in r.trace_dna.model_dump().values():
        assert 0.0 <= float(v) <= 1.0

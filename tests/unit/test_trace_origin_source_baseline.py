from datetime import UTC, datetime, timedelta

from app.services.bastion_trace.evidence_independence import EvidenceIndependenceService
from app.services.bastion_trace.provider_disagreement import ProviderDisagreementService
from app.services.bastion_trace.source_freshness import evaluate_source_freshness


def test_source_freshness_thresholds() -> None:
    now = datetime.now(UTC)
    assert evaluate_source_freshness(now) == "FRESH"
    assert evaluate_source_freshness(now - timedelta(days=3)) == "RECENT"
    assert evaluate_source_freshness(now - timedelta(days=10)) == "STALE"


def test_evidence_independence() -> None:
    svc = EvidenceIndependenceService()
    assert svc.calculate(["a"]).score <= 0.25
    assert svc.calculate(["a", "b", "c"]).score > 0.5


def test_provider_disagreement() -> None:
    svc = ProviderDisagreementService()
    res = svc.detect_disagreement(["exchange", "mixer"], ["LOW", "LOW"])
    assert res.has_disagreement is True
    assert res.manual_review_recommended is True

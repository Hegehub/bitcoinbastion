from app.services.script.descriptor_awareness_service import DescriptorAwarenessService


def test_descriptor_awareness_strong_when_present_fresh_and_complete() -> None:
    out = DescriptorAwarenessService().evaluate(
        has_descriptor=True,
        has_recovery_instructions=True,
        has_backup_reference=True,
        descriptor_age_days=7,
        script_type="p2wpkh",
        wallet_type="single-sig",
    )
    assert out.completeness_score >= 0.8
    assert out.recoverability_assumption == "strong"
    assert out.freshness["freshness_band"] == "fresh"
    assert out.confidence >= 0.75


def test_descriptor_awareness_missing_descriptor_is_degraded_not_fatal() -> None:
    out = DescriptorAwarenessService().evaluate(
        has_descriptor=False,
        has_recovery_instructions=True,
        has_backup_reference=True,
        descriptor_age_days=None,
        script_type="unknown",
        wallet_type="watch-only",
        is_watch_only=True,
    )
    assert out.completeness_score < 0.6
    assert out.recoverability_assumption in {"weak", "moderate"}
    assert out.confidence < 0.7
    assert any("missing" in w.lower() for w in out.warnings)


def test_descriptor_awareness_stale_descriptor_reduces_readiness() -> None:
    fresh = DescriptorAwarenessService().evaluate(
        has_descriptor=True,
        has_recovery_instructions=True,
        has_backup_reference=True,
        descriptor_age_days=10,
        script_type="taproot",
    )
    stale = DescriptorAwarenessService().evaluate(
        has_descriptor=True,
        has_recovery_instructions=True,
        has_backup_reference=True,
        descriptor_age_days=180,
        script_type="taproot",
    )
    assert stale.completeness_score < fresh.completeness_score
    assert stale.confidence < fresh.confidence
    assert stale.freshness["freshness_band"] == "stale"


def test_descriptor_awareness_multisig_partial_without_signer_metadata() -> None:
    out = DescriptorAwarenessService().evaluate(
        has_descriptor=True,
        has_recovery_instructions=True,
        has_backup_reference=True,
        descriptor_age_days=20,
        script_type="p2wsh",
        wallet_type="multisig-2of3",
        multisig_signer_count=None,
    )
    assert out.explainability["signals"]["multisig_completeness"] == "partial"
    assert any("multisig" in w.lower() for w in out.warnings)

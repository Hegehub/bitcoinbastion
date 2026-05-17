from app.schemas.mining import StratumV2CapabilityEvaluationInput
from app.services.mining.stratum_v2_capability_service import StratumV2CapabilityService


def test_stratum_v2_capability_service_verified_case() -> None:
    service = StratumV2CapabilityService()
    result = service.evaluate(
        StratumV2CapabilityEvaluationInput(
            supports_stratum_v2="verified",
            supports_job_declaration="verified",
            supports_template_distribution="supported",
            supports_template_provider="supported",
            supports_translator_proxy="supported",
            supports_encrypted_channel="verified",
            miner_can_build_templates="supported",
            pool_can_override_templates="supported",
            miner_template_control_level="supported",
            source_type="official_pool_docs",
            confidence=0.9,
        )
    )
    assert "Strong Stratum V2 capability posture" in result.capability_summary
    assert result.confidence >= 0.84
    assert result.missing_capabilities == []


def test_stratum_v2_capability_service_claimed_unverified_case() -> None:
    service = StratumV2CapabilityService()
    result = service.evaluate(
        StratumV2CapabilityEvaluationInput(
            supports_stratum_v2="claimed_unverified",
            supports_job_declaration="claimed_unverified",
            supports_template_distribution="claimed_unverified",
            supports_template_provider="claimed_unverified",
            supports_translator_proxy="claimed_unverified",
            supports_encrypted_channel="claimed_unverified",
            miner_can_build_templates="claimed_unverified",
            pool_can_override_templates="claimed_unverified",
            miner_template_control_level="claimed_unverified",
            source_type="unknown",
            confidence=0.6,
        )
    )
    assert "claimed-unverified" in result.capability_summary.lower()
    assert any("no active network probing" in note.lower() for note in result.limitations)
    assert 0.0 <= result.confidence < 0.8


def test_stratum_v2_capability_service_unknown_and_partial_reduce_confidence() -> None:
    service = StratumV2CapabilityService()
    result = service.evaluate(
        StratumV2CapabilityEvaluationInput(
            supports_stratum_v2="partial",
            supports_job_declaration="unknown",
            supports_template_distribution="partial",
            supports_template_provider="unknown",
            supports_translator_proxy="supported",
            supports_encrypted_channel="unknown",
            miner_can_build_templates="partial",
            pool_can_override_templates="unknown",
            miner_template_control_level="partial",
            source_type="manual_entry",
            confidence=0.7,
        )
    )
    assert "partial" in result.capability_summary.lower()
    assert "supports_job_declaration" in result.missing_capabilities
    assert result.confidence < 0.65


def test_stratum_v2_capability_service_unsupported_case() -> None:
    service = StratumV2CapabilityService()
    result = service.evaluate(
        StratumV2CapabilityEvaluationInput(
            supports_stratum_v2="unsupported",
            supports_job_declaration="unsupported",
            supports_template_distribution="unsupported",
            supports_template_provider="unsupported",
            supports_translator_proxy="unsupported",
            supports_encrypted_channel="unsupported",
            miner_can_build_templates="unsupported",
            pool_can_override_templates="unsupported",
            miner_template_control_level="unsupported",
            source_type="pool_api",
            confidence=0.8,
        )
    )
    assert "unsupported dimensions" in result.capability_summary.lower()
    assert len(result.negative_factors) == 9
    assert result.confidence <= 0.5


def test_stratum_v2_capability_service_source_quality_penalties_applied() -> None:
    service = StratumV2CapabilityService()
    result = service.evaluate(
        StratumV2CapabilityEvaluationInput(
            supports_stratum_v2="supported",
            supports_job_declaration="supported",
            supports_template_distribution="supported",
            supports_template_provider="supported",
            supports_translator_proxy="supported",
            supports_encrypted_channel="supported",
            miner_can_build_templates="supported",
            pool_can_override_templates="supported",
            miner_template_control_level="supported",
            source_type="fixture",
            freshness_seconds=999999,
            is_synthetic=True,
            confidence=0.95,
        )
    )
    assert result.confidence < 0.8
    assert any("synthetic_penalty=" in item for item in result.explainability.source_quality_impact)

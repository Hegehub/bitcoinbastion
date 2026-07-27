from datetime import UTC, datetime, timedelta

from app.domain.access.integrity import AccessIntegrityBand, AccessIntegrityContext
from app.services.access.access_integrity import (
    CATEGORY_WEIGHTS,
    AccessIntegrityCache,
    AccessIntegrityEngine,
)

NOW = datetime(2026, 7, 26, 12, tzinfo=UTC)


def healthy_evidence() -> dict[str, object]:
    return {
        "wallet_proof_method": "bip322",
        "wallet_proof_age_seconds": 60,
        "lnurl_signature_valid": True,
        "lnurl_k1_consumed": True,
        "lnurl_action_matched": True,
        "device_status": "active",
        "session_status": "active",
        "entitlement_active": True,
        "policy_state": "current",
        "recovery_state": "configured",
        "privacy_state": "minimized",
        "delegation_state": "bounded",
        "hardening_state": "verified",
    }


def test_weights_bounds_determinism_bands_and_freshness() -> None:
    assert sum(CATEGORY_WEIGHTS.values()) == 100
    engine = AccessIntegrityEngine()
    context = AccessIntegrityContext(
        "hmac:principal", "bitcoin_wallet_principal", healthy_evidence(), NOW
    )
    first, second = engine.calculate(context), engine.calculate(context)
    assert (
        first.score == second.score == 100
        and first.evidence_fingerprint == second.evidence_fingerprint
    )
    assert engine.classify_band(90) is AccessIntegrityBand.EXCELLENT
    assert engine.classify_band(75) is AccessIntegrityBand.STRONG
    assert engine.classify_band(55) is AccessIntegrityBand.GUARDED
    assert engine.classify_band(30) is AccessIntegrityBand.RESTRICTED
    assert engine.classify_band(29) is AccessIntegrityBand.CRITICAL
    assert engine.verify_evidence_freshness(first, NOW + timedelta(minutes=4))


def test_missing_evidence_conservative_not_applicable_and_hard_caps() -> None:
    engine = AccessIntegrityEngine()
    missing = engine.calculate(
        AccessIntegrityContext("hmac:p", "lightning_wallet_principal", {}, NOW)
    )
    assert 0 <= missing.score <= 29
    evidence = healthy_evidence() | {"lnurl_not_applicable": True, "principal_revoked": True}
    capped = engine.calculate(
        AccessIntegrityContext("hmac:p", "bitcoin_wallet_principal", evidence, NOW)
    )
    assert capped.score <= 10 and "principal_revoked" in capped.critical_flags
    seed = engine.calculate(
        AccessIntegrityContext(
            "hmac:p",
            "bitcoin_wallet_principal",
            healthy_evidence() | {"raw_private_material_detected": True},
            NOW,
        )
    )
    assert seed.score == 0


def test_recommendations_and_cache_invalidation() -> None:
    engine, cache = AccessIntegrityEngine(), AccessIntegrityCache()
    result = engine.calculate(
        AccessIntegrityContext(
            "hmac:p",
            "bitcoin_wallet_principal",
            healthy_evidence() | {"session_status": "bearer_only"},
            NOW,
        )
    )
    key = cache.key("hmac:p", policy_epoch=1, revocation_epoch=1)
    cache.put(key, result)
    assert result.score <= 25 and cache.get(key) is result
    assert cache.invalidate("hmac:p", "lnurl_k1_replay_detected") and cache.get(key) is None

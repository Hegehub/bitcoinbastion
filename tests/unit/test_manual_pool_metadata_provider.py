from app.integrations.mining.manual_pool_metadata_provider import ManualPoolMetadataProvider


def test_fixture_records_are_synthetic_and_unverified() -> None:
    provider = ManualPoolMetadataProvider()
    record = provider.from_fixture(
        pool_name="Fixture Pool",
        capability_claims={"supports_stratum_v2": "supported"},
        evidence_refs=[],
        freshness=1200,
    )
    assert record.source_type == "fixture"
    assert record.is_synthetic is True
    assert record.is_verified is False
    assert record.capability_claims["supports_stratum_v2"] == "claimed_unverified"
    assert any("synthetic" in item.lower() for item in record.limitations)


def test_manual_records_mark_claims_unverified_when_no_evidence() -> None:
    provider = ManualPoolMetadataProvider()
    record = provider.from_manual_entry(
        pool_name="Manual Pool",
        capability_claims={"supports_encrypted_channel": "verified"},
        evidence_refs=[],
    )
    assert record.source_type == "manual_entry"
    assert record.capability_claims["supports_encrypted_channel"] == "claimed_unverified"
    assert record.is_verified is False
    assert record.is_synthetic is False


def test_manual_records_keep_supported_claims_with_evidence_refs() -> None:
    provider = ManualPoolMetadataProvider()
    record = provider.from_manual_entry(
        pool_name="Documented Pool",
        capability_claims={"supports_job_declaration": "supported"},
        evidence_refs=["https://example.invalid/proof"],
    )
    assert record.capability_claims["supports_job_declaration"] == "supported"

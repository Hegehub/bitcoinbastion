from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ManualPoolMetadataRecord:
    pool_name: str
    capability_claims: dict[str, str]
    source_type: str
    provider_name: str
    evidence_refs: list[str] = field(default_factory=list)
    is_verified: bool = False
    is_synthetic: bool = False
    freshness: int | None = None
    limitations: list[str] = field(default_factory=list)


class ManualPoolMetadataProvider:
    """Safe provider for manual or fixture-based mining pool capability metadata."""

    def from_fixture(
        self,
        *,
        pool_name: str,
        capability_claims: dict[str, str],
        provider_name: str = "fixture_manual_pool_metadata_provider",
        evidence_refs: list[str] | None = None,
        freshness: int | None = None,
        limitations: list[str] | None = None,
    ) -> ManualPoolMetadataRecord:
        refs = list(evidence_refs or [])
        claims = self._sanitize_claims(capability_claims, source_type="fixture", evidence_refs=refs)
        return ManualPoolMetadataRecord(
            pool_name=pool_name,
            capability_claims=claims,
            source_type="fixture",
            provider_name=provider_name,
            evidence_refs=refs,
            is_verified=False,
            is_synthetic=True,
            freshness=freshness,
            limitations=list(limitations or []) + ["Fixture data is synthetic and non-production evidence."],
        )

    def from_manual_entry(
        self,
        *,
        pool_name: str,
        capability_claims: dict[str, str],
        provider_name: str = "manual_pool_metadata_provider",
        evidence_refs: list[str] | None = None,
        freshness: int | None = None,
        limitations: list[str] | None = None,
    ) -> ManualPoolMetadataRecord:
        refs = list(evidence_refs or [])
        claims = self._sanitize_claims(capability_claims, source_type="manual_entry", evidence_refs=refs)
        return ManualPoolMetadataRecord(
            pool_name=pool_name,
            capability_claims=claims,
            source_type="manual_entry",
            provider_name=provider_name,
            evidence_refs=refs,
            is_verified=False,
            is_synthetic=False,
            freshness=freshness,
            limitations=list(limitations or []) + ["Manual entry is advisory and requires independent verification."],
        )

    @staticmethod
    def _sanitize_claims(
        claims: dict[str, str],
        *,
        source_type: str,
        evidence_refs: list[str],
    ) -> dict[str, str]:
        sanitized: dict[str, str] = {}
        for key, value in claims.items():
            status = str(value)
            if status == "verified" and not evidence_refs:
                status = "claimed_unverified"
            if source_type in {"manual_entry", "fixture"} and status == "supported" and not evidence_refs:
                status = "claimed_unverified"
            sanitized[str(key)] = status
        return sanitized

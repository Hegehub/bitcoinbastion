from __future__ import annotations

from app.db.repositories.mining_repository import MiningRepository
from app.db.session import SessionLocal
from app.integrations.mining.manual_pool_metadata_provider import ManualPoolMetadataProvider
from app.services.mining.pool_registry_service import MiningPoolRegistryService
from app.tasks.celery_app import celery_app


def _load_manual_static_metadata(provider: ManualPoolMetadataProvider) -> list[dict[str, object]]:
    fixture_record = provider.from_fixture(
        pool_name="Fixture Pool Alpha",
        capability_claims={
            "supports_stratum_v2": "claimed_unverified",
            "supports_job_declaration": "unknown",
            "supports_translator_proxy": "claimed_unverified",
            "supports_encrypted_channel": "unknown",
        },
        evidence_refs=["fixture:mining:pool_alpha"],
        freshness=3600,
    )
    manual_record = provider.from_manual_entry(
        pool_name="Manual Pool Beta",
        capability_claims={
            "supports_stratum_v2": "claimed_unverified",
            "supports_job_declaration": "claimed_unverified",
            "supports_translator_proxy": "unknown",
            "supports_encrypted_channel": "unknown",
        },
        evidence_refs=["manual:mining:pool_beta"],
        freshness=3600,
    )
    return [
        {
            "pool_name": fixture_record.pool_name,
            "capability_claims": fixture_record.capability_claims,
            "source_type": fixture_record.source_type,
            "provider_name": fixture_record.provider_name,
            "evidence_refs": fixture_record.evidence_refs,
            "is_verified": fixture_record.is_verified,
            "is_synthetic": fixture_record.is_synthetic,
            "freshness": fixture_record.freshness,
            "limitations": fixture_record.limitations,
        },
        {
            "pool_name": manual_record.pool_name,
            "capability_claims": manual_record.capability_claims,
            "source_type": manual_record.source_type,
            "provider_name": manual_record.provider_name,
            "evidence_refs": manual_record.evidence_refs,
            "is_verified": manual_record.is_verified,
            "is_synthetic": manual_record.is_synthetic,
            "freshness": manual_record.freshness,
            "limitations": manual_record.limitations,
        },
    ]


def run_refresh_stratum_v2_capabilities() -> dict[str, int | list[str]]:
    provider = ManualPoolMetadataProvider()
    payloads = _load_manual_static_metadata(provider)
    processed = 0
    created = 0
    updated = 0
    failed = 0
    warnings: list[str] = []

    with SessionLocal() as db:
        service = MiningPoolRegistryService(MiningRepository(db))
        for item in payloads:
            try:
                processed += 1
                result = service.upsert_pool_capability_metadata(item)
                if int(result.get("endpoint_count", 0)) > 0:
                    updated += 1
                else:
                    created += 1
                if str(item.get("source_type")) in {"fixture", "manual_entry"} and bool(item.get("is_verified", False)):
                    warnings.append(f"{item.get('pool_name')}: verified flag ignored for manual/fixture source")
            except Exception as exc:
                failed += 1
                warnings.append(f"{item.get('pool_name', 'unknown')}: {exc}")
                continue

    return {"processed": processed, "created": created, "updated": updated, "failed": failed, "warnings": warnings}


@celery_app.task(name="tasks.mining.refresh_stratum_v2_capabilities")  # type: ignore[untyped-decorator]
def refresh_stratum_v2_capabilities() -> dict[str, int | list[str]]:
    return run_refresh_stratum_v2_capabilities()

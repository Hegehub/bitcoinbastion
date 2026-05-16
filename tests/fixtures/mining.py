"""Synthetic mining fixture data for local tests only.

Important:
- These records are synthetic fixtures, not real-world mining intelligence.
- Values intentionally include unknown/unverified states.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class MiningFixturePool:
    pool_key: str
    display_name: str
    provider_name: str
    sv2_state: str
    template_control_state: str
    template_control_owner: str
    source_quality: dict[str, object]


def _source_quality(*, confidence: float) -> dict[str, object]:
    return {
        "source_type": "synthetic",
        "provider_name": "fixture_synthetic",
        "is_verified": False,
        "is_fallback": False,
        "is_synthetic": True,
        "confidence": confidence,
        "freshness": {
            "observed_at": datetime.now(UTC).isoformat(),
            "age_seconds": 0,
            "freshness_band": "unknown",
        },
        "limitations": [
            "Synthetic fixture data for local/unit tests only",
            "Not real pool intelligence",
        ],
        "evidence_refs": ["fixture://mining/synthetic"],
    }


def mining_pool_fixtures() -> list[MiningFixturePool]:
    return [
        MiningFixturePool(
            pool_key="examplepool",
            display_name="ExamplePool",
            provider_name="fixture_synthetic",
            sv2_state="unknown",
            template_control_state="unknown",
            template_control_owner="unknown",
            source_quality=_source_quality(confidence=0.2),
        ),
        MiningFixturePool(
            pool_key="sv2pool",
            display_name="SV2Pool",
            provider_name="fixture_synthetic",
            sv2_state="claimed_unverified",
            template_control_state="shared_control_partial",
            template_control_owner="shared",
            source_quality=_source_quality(confidence=0.45),
        ),
        MiningFixturePool(
            pool_key="legacypool",
            display_name="LegacyPool",
            provider_name="fixture_synthetic",
            sv2_state="unsupported",
            template_control_state="pool_controlled",
            template_control_owner="pool",
            source_quality=_source_quality(confidence=0.35),
        ),
        MiningFixturePool(
            pool_key="mixedpool",
            display_name="MixedPool",
            provider_name="fixture_synthetic",
            sv2_state="partial",
            template_control_state="shared_control_partial",
            template_control_owner="shared",
            source_quality=_source_quality(confidence=0.4),
        ),
    ]

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.access import (
    AccessMeResponse,
    ChildApiKeyPublic,
    RecoveryStatusResponse,
    SubscriptionEntitlementResponse,
)


TEMPORAL_FIELDS = {
    "AccessMeResponse": ("session_expires_at",),
    "AccessPaymentIntentStatusResponse": ("expires_at",),
    "ChildApiKeyPublic": ("created_at", "expires_at"),
    "DelegatedPassPublic": ("valid_from", "expires_at"),
    "RecoveryStatusResponse": ("cooldown_until",),
    "SubscriptionEntitlementResponse": ("valid_from", "valid_until", "created_at"),
}


def test_access_temporal_openapi_contracts_are_date_times() -> None:
    schemas = app.openapi()["components"]["schemas"]
    for model, fields in TEMPORAL_FIELDS.items():
        for field in fields:
            schema = schemas[model]["properties"][field]
            branches = schema.get("anyOf", [schema])
            temporal = [branch for branch in branches if branch.get("type") != "null"]
            assert len(temporal) == 1, (model, field)
            assert temporal[0]["type"] == "string", (model, field)
            assert temporal[0]["format"] == "date-time", (model, field)


def test_temporal_models_parse_iso_datetime_and_preserve_null() -> None:
    now = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
    me = AccessMeResponse(
        certificate_fingerprint="cert",
        plan_code="free",
        entitlement_status="active",
        active_scopes=[],
        device_status="active",
        session_expires_at=now.isoformat(),
        access_integrity_summary={},
        recovery_status_summary={},
    )
    assert me.session_expires_at == now
    status = RecoveryStatusResponse(
        recovery_attempt_id="attempt",
        status="started",
        threshold=2,
        verified_factor_count=0,
        missing_factor_count=2,
        decision="pending",
        reason="threshold_not_met",
        cooldown_until=None,
    )
    assert status.cooldown_until is None


def test_malformed_temporal_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChildApiKeyPublic(
            key_id="key",
            scopes=[],
            status="active",
            created_at="not-a-time",
            expires_at="not-a-time",
        )


def test_entitlement_temporal_fields_are_required() -> None:
    with pytest.raises(ValidationError):
        SubscriptionEntitlementResponse(
            plan_code="free",
            status="active",
            metric_groups=[],
            scopes=[],
            limits={},
            crypto_epoch=1,
        )

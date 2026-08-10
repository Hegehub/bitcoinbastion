from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from bastion_ui.components.security.access_required import access_required_shell
from bastion_ui.domain.access.security import (
    EntitlementPosture,
    OperationProofPosture,
    ProofOfPossessionPosture,
    SecurityPostureViewModel,
    SessionPosture,
    adapt_access_me,
)
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.security.requirements import requirement_for
from bastion_ui.transport.foundation import SafeTransportError
from bastion_ui.transport.generated_http import GetMeApiV1AccessMeGetSuccess
from bastion_ui.transport.generated_schemas import AccessMeResponse

NOW = datetime(2026, 8, 10, tzinfo=UTC)


def response(
    *, entitlement: str = "active", device: str = "active"
) -> GetMeApiV1AccessMeGetSuccess:
    return GetMeApiV1AccessMeGetSuccess(
        root=AccessMeResponse(
            access_integrity_summary={},
            active_scopes=["read:profile"],
            certificate_fingerprint="safe-public-fingerprint",
            device_status=device,
            entitlement_status=entitlement,
            plan_code="basic_pass",
            recovery_status_summary={},
            session_expires_at=NOW + timedelta(hours=1),
        )
    )


def live() -> Provenance:
    return Provenance(state=ProvenanceState.LIVE, source_label="Access", observed_at=NOW)


def test_security_dimensions_are_distinct_and_no_universal_auth_boolean() -> None:
    fields = SecurityPostureViewModel.model_fields
    assert "is_authenticated" not in fields and "has_access" not in fields
    assert {
        "session",
        "entitlement",
        "capabilities",
        "pop",
        "human_intent",
        "step_up",
    } <= fields.keys()
    assert len({SessionPosture.UNKNOWN, SessionPosture.ABSENT}) == 2
    assert len(
        {OperationProofPosture.REQUIRED, OperationProofPosture.SATISFIED_FOR_CURRENT_OPERATION}
    ) == 2


def test_access_adapter_preserves_authoritative_distinctions() -> None:
    posture = adapt_access_me(response(entitlement="restricted"), live())
    assert posture.session is SessionPosture.ACTIVE
    assert posture.entitlement is EntitlementPosture.RESTRICTED
    assert posture.capabilities == ("read:profile",)
    assert posture.pop is ProofOfPossessionPosture.UNKNOWN
    assert posture.human_intent is OperationProofPosture.NOT_REQUIRED
    assert posture.step_up is OperationProofPosture.UNKNOWN


def test_revocation_wins_and_entitlement_or_pop_never_grants_everything() -> None:
    revoked = adapt_access_me(response(device="revoked"), live())
    assert revoked.session is SessionPosture.REVOKED
    assert revoked.entitlement is EntitlementPosture.ACTIVE
    assert revoked.capabilities == ("read:profile",)
    assert revoked.pop is not ProofOfPossessionPosture.SATISFIED


def test_browser_dump_is_allowlisted_and_rejects_secret_fields() -> None:
    posture = adapt_access_me(response(), live())
    dumped = posture.browser_dump()
    serialized = str(dumped).lower()
    for forbidden in ("session_secret", "nonce", "private_key", "payment_proof", "signature"):
        assert forbidden not in serialized
    with pytest.raises(ValidationError):
        SecurityPostureViewModel.model_validate({**posture.model_dump(), "session_secret": "bad"})


def test_route_requirements_are_authoritative_and_unknown_fails_closed() -> None:
    public = requirement_for("/")
    protected = requirement_for("/access/security-posture")
    unknown = requirement_for("/new-protected-route")
    assert public.public
    assert not protected.public
    assert protected.operation_id == "get_me_api_v1_access_me_get"
    assert protected.security_profile == "access-session:get_me_api_v1_access_me_get"
    assert not unknown.public and unknown.security_profile is None


def test_backend_denial_overrides_optimistic_posture() -> None:
    posture = adapt_access_me(response(), live())
    assert posture.session is SessionPosture.ACTIVE
    lifecycle, safe = project_transport_error(
        SafeTransportError(403, "revoked", False, "Access revoked")
    )
    assert lifecycle is LifecycleStatus.FORBIDDEN
    assert safe.summary == "Access revoked"


def test_access_required_surface_is_accessible_and_contains_no_protected_content() -> None:
    rendered = str(access_required_shell("Access required", "No active session"))
    assert "Access required" in rendered
    assert "role" in rendered and "alert" in rendered
    assert "security-recovery" in rendered
    assert "protected-content" not in rendered

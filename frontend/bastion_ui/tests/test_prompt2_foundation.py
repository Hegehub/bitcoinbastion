from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import get_type_hints

import httpx
import pytest
from pydantic import ValidationError

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.domain.access.adapters import adapt_child_key_created
from bastion_ui.domain.lifecycle import (
    LatestRequestWins,
    LifecycleStatus,
    execute_with_bounded_retry,
    project_transport_error,
)
from bastion_ui.domain.operations.adapters import adapt_intelligence_health
from bastion_ui.domain.overview.adapters import adapt_public_status
from bastion_ui.domain.overview.models import PublicStatusViewModel
from bastion_ui.domain.ownership import DOMAIN_ADAPTER_OWNERS
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.state.prompt2_status_state import Prompt2StatusState
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    HEALTHAPIV1HEALTHGET_OPERATION,
    PUBLICSTATUSAPIV1PUBLICSTATUSGET_OPERATION,
    HealthApiV1HealthGetSuccess,
    IntelligenceHealthIntelligenceGetSuccess,
    PublicStatusApiV1PublicStatusGetRequest,
    PublicStatusApiV1PublicStatusGetSuccess,
    public_status_api_v1_public_status_get,
)
from bastion_ui.transport.generated_schemas import (
    ChildApiKeyCreateResponse,
    IntelligenceHealthOut,
    PublicStatusResponse,
    ResponseEnvelopePublicStatusResponse,
)

NOW = datetime(2026, 8, 9, 18, 0, tzinfo=UTC)


def status_response(
    *,
    calibrated: bool = False,
    modules: dict[str, str] | None = None,
    limitations: list[str] | None = None,
) -> PublicStatusApiV1PublicStatusGetSuccess:
    return PublicStatusApiV1PublicStatusGetSuccess(
        root=ResponseEnvelopePublicStatusResponse(
            success=True,
            data=PublicStatusResponse(
                known_limitations=limitations,
                last_update=NOW,
                modules=modules or {},
                platform_status="degraded",
                production_calibrated=calibrated,
                trace_status="partial",
            ),
        )
    )


def test_domain_ownership_is_explicit_and_payregister_isolated() -> None:
    assert set(DOMAIN_ADAPTER_OWNERS) == {
        "Overview", "Operations", "Market", "Trace", "Evidence",
        "Access", "Console", "LNURL", "PayRegister",
    }
    assert DOMAIN_ADAPTER_OWNERS["PayRegister"] != DOMAIN_ADAPTER_OWNERS["Overview"]


def test_public_status_adapter_preserves_false_empty_null_map_and_time() -> None:
    view = adapt_public_status(status_response(), observed_at=NOW)
    assert view.production_calibrated is False
    assert view.modules == ()
    assert view.known_limitations is None
    assert view.last_update == NOW
    assert view.provenance.state is ProvenanceState.LIVE
    assert view.browser_dump()["modules"] == []


def test_operations_adapter_preserves_decimal_time_and_quality() -> None:
    response = IntelligenceHealthIntelligenceGetSuccess(
        root=IntelligenceHealthOut(
            degraded_state=True,
            last_failure=None,
            last_success=NOW,
            operational_limitations=[],
            provider_confidence=Decimal("0.1250"),
            status="partial",
        )
    )
    view = adapt_intelligence_health(response)
    assert view.provider_confidence == Decimal("0.1250")
    assert view.degraded is True
    assert view.last_success == NOW
    assert view.last_failure is None
    assert view.limitations == ()


def test_sensitive_child_secret_is_not_projected_or_serialized() -> None:
    response = ChildApiKeyCreateResponse(
        key_id="safe-id",
        raw_child_api_key="never-browser-state",
        scopes=["read"],
        limits={},
        expires_at=NOW,
        warning="display once",
    )
    view = adapt_child_key_created(response)
    dumped = view.model_dump(mode="json")
    assert "raw_child_api_key" not in dumped
    assert "never-browser-state" not in repr(view)
    assert "never-browser-state" not in str(dumped)


def test_provenance_has_exactly_four_states_and_strict_authority() -> None:
    assert set(ProvenanceState) == {
        ProvenanceState.LIVE,
        ProvenanceState.VERIFIED_SNAPSHOT,
        ProvenanceState.DEMO_FIXTURE,
        ProvenanceState.UNAVAILABLE,
    }
    assert issubclass(ProvenanceState, StrEnum)
    live = Provenance(state=ProvenanceState.LIVE, source_label="runtime", observed_at=NOW)
    fixture = Provenance(state=ProvenanceState.DEMO_FIXTURE, source_label="test")
    unavailable = Provenance(
        state=ProvenanceState.UNAVAILABLE,
        source_label="none",
        unavailable_reason="backend unreachable",
    )
    snapshot = Provenance(
        state=ProvenanceState.VERIFIED_SNAPSHOT,
        source_label="snapshot",
        captured_at=NOW,
        source_revision="revision",
        integrity_reference="sha256:abc",
    )
    assert live.state is ProvenanceState.LIVE
    assert fixture.state is not ProvenanceState.LIVE
    assert unavailable.browser_dump()["state"] == "UNAVAILABLE"
    assert snapshot.state is ProvenanceState.VERIFIED_SNAPSHOT
    with pytest.raises(ValidationError):
        Provenance(state=ProvenanceState.VERIFIED_SNAPSHOT, source_label="cache")
    with pytest.raises(ValidationError):
        Provenance(state=ProvenanceState.UNAVAILABLE, source_label="none")


def test_section_level_provenance_needs_no_mixed_state() -> None:
    sections = {
        "live": Provenance(state=ProvenanceState.LIVE, source_label="runtime"),
        "demo": Provenance(state=ProvenanceState.DEMO_FIXTURE, source_label="fixture"),
    }
    assert sections["live"].state is ProvenanceState.LIVE
    assert sections["demo"].state is ProvenanceState.DEMO_FIXTURE
    assert "MIXED" not in ProvenanceState.__members__


def test_safe_error_mapping_keeps_http_classes_distinct() -> None:
    expected = {
        401: LifecycleStatus.UNAUTHORIZED,
        403: LifecycleStatus.FORBIDDEN,
        404: LifecycleStatus.NOT_FOUND,
        409: LifecycleStatus.CONFLICT,
        422: LifecycleStatus.VALIDATION_ERROR,
        429: LifecycleStatus.RATE_LIMITED,
        500: LifecycleStatus.SERVER_ERROR,
    }
    for status, lifecycle in expected.items():
        projected, error = project_transport_error(
            SafeTransportError(status, f"http_{status}", status >= 429, "Safe summary")
        )
        assert projected is lifecycle
        assert error.summary == "Safe summary"


def test_latest_request_wins_and_cancel_invalidates_old_tokens() -> None:
    requests: LatestRequestWins[str] = LatestRequestWins()
    first = requests.begin()
    second = requests.begin()
    assert not requests.is_current(first)
    assert requests.is_current(second)
    requests.cancel()
    assert not requests.is_current(second)


@pytest.mark.asyncio
async def test_bounded_retry_and_mutation_no_auto_retry() -> None:
    attempts = 0

    async def flaky() -> HealthApiV1HealthGetSuccess:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise SafeTransportError(503, "http_503", True, "Retryable")
        return HealthApiV1HealthGetSuccess.model_validate(
            {"app": "bastion", "details": {}, "status": "ok"}
        )

    await execute_with_bounded_retry(HEALTHAPIV1HEALTHGET_OPERATION, flaky)
    assert attempts == 2

    attempts = 0
    mutation = replace(HEALTHAPIV1HEALTHGET_OPERATION, method="POST", retry_safe=True)
    with pytest.raises(SafeTransportError):
        await execute_with_bounded_retry(mutation, flaky)
    assert attempts == 1


@pytest.mark.asyncio
async def test_canonical_client_to_adapter_harness_uses_real_transport_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/public/status"
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "known_limitations": ["provider degraded"],
                    "last_update": NOW.isoformat(),
                    "modules": {"trace": "partial"},
                    "platform_status": "degraded",
                    "production_calibrated": False,
                    "trace_status": "partial",
                },
            },
        )

    async with httpx.AsyncClient(
        base_url="http://bastion.test", transport=httpx.MockTransport(handler)
    ) as client:
        result = await public_status_api_v1_public_status_get(
            HttpTransport(client), PublicStatusApiV1PublicStatusGetRequest()
        )
    view = adapt_public_status(result, observed_at=NOW)
    assert PUBLICSTATUSAPIV1PUBLICSTATUSGET_OPERATION.path == "/api/v1/public/status"
    assert view.platform_status == "degraded"
    assert view.modules == (("trace", "partial"),)


def test_state_and_badge_use_safe_view_model_boundary() -> None:
    assert get_type_hints(Prompt2StatusState)["view_model"] == PublicStatusViewModel | None
    component = provenance_badge("LIVE", source="runtime", details="informational")
    rendered = str(component)
    assert "LIVE" in rendered
    assert "aria-label" in rendered
    assert "tabIndex" in rendered or "tab_index" in rendered

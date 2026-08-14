from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from bastion_ui.domain.operations.adapters import adapt_health, adapt_providers, adapt_storage
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.route_lifecycle import transition_actions
from bastion_ui.topology import ROUTE_BY_ID, validate_dependencies, validate_routes
from bastion_ui.transport.generated_http import (
    HealthApiV1HealthGetSuccess,
    ProvidersApiV1HealthProvidersGetSuccess,
    StorageStatusApiV1StorageStatusGetSuccess,
)
from bastion_ui.transport.generated_schemas import (
    HealthOut,
    ProviderHealthSnapshotOut,
    StorageDegradedMode,
    StorageRole,
    StorageStatusResponse,
    StorageStatusSummary,
    StorageStatusValue,
    StorageStoreStatus,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 8, 11, tzinfo=UTC)


def test_prompt8_routes_and_canonical_dependencies() -> None:
    validate_routes()
    validate_dependencies()
    expected = {
        "overview.home": 3,
        "operations": 3,
        "operations.health": 1,
        "operations.providers": 1,
        "operations.storage": 1,
    }
    for route_id, dependency_count in expected.items():
        route = ROUTE_BY_ID[route_id]
        assert route.security_requirement_id == "public"
        assert len(route.http_operations) == dependency_count


def test_health_adapter_preserves_authoritative_status_and_zero_values() -> None:
    result = adapt_health(
        HealthApiV1HealthGetSuccess(
            root=HealthOut(app="Bitcoin Bastion", status="critical", details={"queue": "0"})
        ),
        observed_at=NOW,
    )
    assert result.status == "critical"
    assert result.details == (("queue", "0"),)
    assert result.provenance.state is ProvenanceState.LIVE


def test_provider_adapter_preserves_optional_and_numeric_semantics() -> None:
    result = adapt_providers(
        ProvidersApiV1HealthProvidersGetSuccess(
            root=[
                ProviderHealthSnapshotOut(
                    provider_name="local-node",
                    provider_type="bitcoin_rpc",
                    health_state="degraded",
                    avg_latency_ms=Decimal("0"),
                    failure_count=0,
                    last_success_at=None,
                )
            ]
        ),
        observed_at=NOW,
    )
    provider = result.providers[0]
    assert provider.latency_ms == Decimal("0")
    assert provider.last_success_at is None
    assert provider.state == "degraded"


def test_storage_adapter_excludes_driver_details_and_preserves_unknown() -> None:
    response = StorageStatusApiV1StorageStatusGetSuccess(
        root=StorageStatusResponse(
            status=StorageStatusValue(root="unknown"),
            profile="self_hosted",
            summary=StorageStatusSummary(
                required_ok=False, optional_degraded=True, critical_failures=0, warnings=1
            ),
            stores={
                "postgres": StorageStoreStatus(
                    status=StorageStatusValue(root="unknown"),
                    role=StorageRole(root="required"),
                    purpose="canonical operational persistence",
                    latency_ms=None,
                    details={"connection_url": "postgres://secret", "path": "/private"},
                )
            },
            degraded_mode=StorageDegradedMode(
                active=True, reason="metrics unavailable", impact=["capacity unknown"]
            ),
        )
    )
    result = adapt_storage(response, observed_at=NOW)
    dumped = result.model_dump_json()
    assert result.status == "unknown"
    assert result.stores[0].latency_ms is None
    assert "connection_url" not in dumped
    assert "postgres://secret" not in dumped
    assert "/private" not in dumped


def test_route_transitions_load_only_owned_prompt8_sections() -> None:
    assert transition_actions("overview.home", "operations.providers").invalidate_http is True
    source = (ROOT / "frontend/bastion_ui/route_lifecycle.py").read_text()
    assert 'route_id == "operations.providers"' in source
    assert "ProvidersState.load" in source


def test_production_screens_have_no_fake_operational_metrics() -> None:
    files = [
        ROOT / "frontend/bastion_ui/routes/home.py",
        ROOT / "frontend/bastion_ui/routes/operations.py",
        ROOT / "frontend/bastion_ui/components/operations/screens.py",
    ]
    text = "\n".join(path.read_text().lower() for path in files)
    forbidden = ("all systems operational", "99.9%", "fake provider", "demo_fixture")
    assert not any(value in text for value in forbidden)


def test_endpoint_to_dom_lineage_is_named() -> None:
    source = (ROOT / "frontend/bastion_ui/components/operations/screens.py").read_text()
    for marker in ("health-status", "health-application", "storage-status", "storage-profile"):
        assert marker in source

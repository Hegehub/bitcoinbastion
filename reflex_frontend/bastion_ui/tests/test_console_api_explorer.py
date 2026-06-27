from __future__ import annotations

from bastion_ui.components.console.api_endpoint_card import SAFE_READ_ENDPOINTS
from bastion_ui.components.console.api_explorer_panel import API_EXPLORER_SAFETY_COPY
from bastion_ui.services.api_explorer_client import ApiExplorerApiClient


def test_api_explorer_safety_copy_warns_against_sensitive_material() -> None:
    assert "safe read-only calls" in API_EXPLORER_SAFETY_COPY
    assert "Never submit seed phrases" in API_EXPLORER_SAFETY_COPY
    assert "private keys" in API_EXPLORER_SAFETY_COPY
    assert "wallet files" in API_EXPLORER_SAFETY_COPY
    assert "signing material" in API_EXPLORER_SAFETY_COPY


def test_api_explorer_only_safe_reads_are_tryable() -> None:
    catalog = ApiExplorerApiClient().endpoint_catalog()
    for endpoint in catalog:
        if endpoint.tryable:
            assert endpoint.safety == "Safe read"
            assert endpoint.path in {item.removeprefix("GET ") for item in SAFE_READ_ENDPOINTS}
        else:
            assert endpoint.safety != "Safe read" or "{" in endpoint.path

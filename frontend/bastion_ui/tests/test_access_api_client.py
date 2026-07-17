from __future__ import annotations

from bastion_ui.access_client import AccessApiClient


def test_access_client_uses_access_layer_endpoints() -> None:
    client = AccessApiClient(base_url="https://api.example.test")
    assert client._url("/v1/access/payment-intents") == "https://api.example.test/v1/access/payment-intents"


def test_access_client_exposes_required_methods() -> None:
    required = {
        "create_payment_intent",
        "get_payment_intent",
        "issue_certificate",
        "create_challenge",
        "create_session",
        "get_access_me",
        "get_access_entitlements",
        "get_access_limits",
        "start_recovery",
        "get_recovery_status",
        "lockdown",
    }
    assert required.issubset(set(dir(AccessApiClient)))
